import fitparse


def show_ele_data(data):
    if data.units:
        print(" * {}: {} ({})".format(data.name, data.value, data.units))
    else:
        print(" * {}: {}".format(data.name, data.value))


if __name__ == "__main__":
    # Load the FIT file
    fitfile = fitparse.FitFile("./data/<ACTIVITY_NAME>.fit")

    # Iterate over all messages of type "record"
    # (other types include "device_info", "file_creator", "event", etc)
    for record in fitfile.get_messages("record"):
        # last_data = record
        # show_ele_data(last_data)
        # Records can contain multiple pieces of data (ex: timestamp, latitude, longitude, etc)
        for data in record:
            show_ele_data(data)
        #     # Print the name and value of the data (and the units if it has any)
        #     if data.units:
        #         print(" * {}: {} ({})".format(data.name, data.value, data.units))
        #     else:
        #         print(" * {}: {}".format(data.name, data.value))

        print("---")
