# coding: utf-8

# Copyright (c) 2019-2020 Latona. All rights reserved.
import time

from aion.logger import lprint
from aion.microservice import Options, main_decorator

from .check import UpdateUsbStateToDB, UsbConnectionMonitor, DATABASE

SERVICE_NAME = "check-usb-storage-connection"
EXECUTE_INTERVAL = 5


def fillter_new_mountpoint(mountpoints, connected_usbs):
    exist_mountpoints = list(map(lambda x: x['mountpoint'], connected_usbs))
    new_mountpoints = []
    for mount in mountpoints:
        if mount not in exist_mountpoints:
            new_mountpoints.append(mount)
    return new_mountpoints


@main_decorator(SERVICE_NAME)
def main_without_kanban(opt: Options):
    lprint("start main_with_kanban()")
    # get cache kanban
    conn = opt.get_conn()
    num = opt.get_number()
    # kanban = conn.get_one_kanban(SERVICE_NAME, num)
    kanban = conn.set_kanban(SERVICE_NAME, num)

    #  main function  #
    usb = UsbConnectionMonitor()
    while True:
        is_change = False
        mountpoints = usb.get_mount_points()
        with UpdateUsbStateToDB() as db:
            con_usbs = db.get_connected_usb_list()
            # connected usb
            new_mountpoints = fillter_new_mountpoint(mountpoints, con_usbs)
            for mount in new_mountpoints:
                db.update_usb_state(mount, 1)
                lprint(f"found usb at:{mount}")
                is_change = True
            db.commit_query()
            # unconnected usb
            for conneted in con_usbs:
                if conneted['mountpoint'] not in mountpoints:
                    db.update_unmounted_usb_state(conneted['usb_id'])
                    lprint(f"unconnected usb at: {conneted['mountpoint']}")
                    is_change = True
            db.commit_query()
        if is_change:
            # output after kanban
            conn.output_kanban(
                result=True,
                process_number=num,
                metadata={"mountpoints": mountpoints, "mode": "all",
                          "database": DATABASE, "table": "usbs"},
            )
        time.sleep(EXECUTE_INTERVAL)


if __name__ == "__main__":
    main_without_kanban()
