import sqlite3
import os
from measure_tool.wildfrag_data import *



queries = {
    "retrieve system": "SELECT * FROM Systems WHERE id = ?;",
    "retrieve devices": "SELECT * FROM StorageDevices WHERE system_id = ?;",
    "retrieve volumes": "SELECT * FROM Volumes WHERE storage_device_id = ?;",
    "retrieve notes": "SELECT * FROM VolumeNotes WHERE volume_id = ?;",
    "retrieve files": "SELECT * FROM Files WHERE volume_id = ?;"
}


class WildFrag:
    db_path : str
    connection = None
    cursor = None

    def __init__(self, database_path):
        self.db_path = database_path

        if not os.path.isfile(database_path):
            raise Exception(f"The file \"{database_path}\" does not exist.")

        self.__connect()
        self.__check_integrity()
        
    def __connect(self):
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()

    def __check_integrity(self):
        self.cursor.execute("pragma integrity_check;")
        result = self.cursor.fetchone()[0]

        if result != "ok":
            raise Exception("Database integrity check failed for database " +
                            f"\"{self.db_path}\".")
    
    def retrieve_system(self, id):
        d = self.select("retrieve system", id).fetchone()

        system = System(d[0], d[1], d[2], d[3])
        system.devices = self.__retrieve_devices(id)
        return system

    def __retrieve_devices(self, system_id):
        devices = []

        # Build up a list of devices...
        result = self.select("retrieve devices", system_id).fetchall()
        for row in result:
            devices.append(StorageDevice(
                row[0], row[1], row[2], row[3], row[4], row[5], row[6]
            ))
        
        # Each system is meant to have at least one device
        assert(len(devices) != 0)

        # Find the volumes of each device...
        # This is in a separate for-loop because it also uses the DB cursor.
        for device in devices:
            device.volumes = self.__retrieve_volumes(device.id)
        
        return devices

    def __retrieve_volumes(self, device_id):
        volumes = []

        # Build up a list of volumes...
        result = self.select("retrieve volumes", device_id).fetchall()
        for row in result:
            volumes.append(Volume(
                row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]
            ))

        # Find the files of each device...
        # This is in a separate for-loop because it also uses the DB cursor.
        for volume in volumes:
            volume.files = self.__retrieve_files(volume.id)

        return volumes
    
    def __retrieve_files(self, volume_id):
        files = []

        # Build up a list of files...
        result = self.select("retrieve files", volume_id).fetchall()
        for r in result:
            files.append(File(
                r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9],
                r[10], r[11], r[12], r[13], r[14], r[15], r[16], r[17], r[18],
                r[19], r[20], r[21], r[22], r[23], r[24], r[25]
            ))

        return files

    def select(self, query_name, *query_args):
        self.cursor.execute(queries[query_name], query_args)
        return self.cursor

        



