import os

import aion.mysql as mysql
from aion.logger import lprint, lprint_exception

DATABASE = "sukibaAnalytics"
MEDIA_PATH = '/media'
MAX_SEARCH_DEPTH = 2

# exclude for jetson special mount
EXCLUDE_MOUNTPOINT = "README"


class UsbConnectionMonitor():

    def get_mount_points(self):
        _moutns = self.search_mount_point(MEDIA_PATH, 0)
        mounts = self.exclude_mount_point(_moutns)
        return mounts

    def search_mount_point(self, path, depth=0):
        mounts = []
        try:
            for entry in os.scandir(path):
                if os.path.ismount(entry.path):
                    mounts.append(entry.path)
                elif entry.is_dir():
                    if depth < MAX_SEARCH_DEPTH:
                        mounts.extend(self.search_mount_point(
                            entry.path, depth=depth+1))
                else:
                    pass
        except PermissionError as e:
            lprint_exception(e)
            return []

        return mounts

    def exclude_mount_point(self, mounts):
        mounts = list(
            filter(lambda mount: EXCLUDE_MOUNTPOINT not in mount, mounts))
        return mounts


class UpdateUsbStateToDB(mysql.BaseMysqlAccess):

    def __init__(self):
        super().__init__(DATABASE)

    def update_usb_state(self, mountpoint, state):
        query = """
                INSERT INTO usbs(mountpoint, state)
                    VALUES (%(mountpoint)s, %(state)s)
                ON DUPLICATE KEY UPDATE
                    mountpoint = values(mountpoint),
                    state = values(state),
                    timestamp = CURRENT_TIMESTAMP();
                """
        args = {'mountpoint': mountpoint, 'state': state}
        self.set_query(query, args)

    def update_unmounted_usb_state(self, usb_id):
        query = """
                UPDATE usbs
                SET state = 0
                WHERE usb_id = %(usb_id)s;
                """
        args = {'usb_id': usb_id}
        self.set_query(query, args)

    def get_connected_usb_list(self):
        query = """
                SELECT * FROM usbs
                WHERE state = 1;
                """
        return self.get_query_list(10, query)


if __name__ == "__main__":
    usb = UsbConnectionMonitor()
    mounts = usb.search_mount_point(MEDIA_PATH, 0)
    print("mount points are: ", mounts)
    mounts = usb.exclude_mount_point(mounts)
    print("mount point excluded are: ", mounts)

    with UpdateUsbStateToDB() as db:
        for mount in mounts:
            db.update_usb_state(mount, 1)
            print("update usb: ", mount)
        db.commit_query()

    with UpdateUsbStateToDB() as db:
        usbs = db.get_connected_usb_list()
        for usb in usbs:
            print(usb)
        db.update_unmounted_usb_state(6)
        db.commit_query()
