from garmin_fit_sdk import Decoder, Stream


def show_ele_data(data):
    if data.units:
        print(" * {}: {} ({})".format(data.name, data.value, data.units))
    else:
        print(" * {}: {}".format(data.name, data.value))


def parser_file(file_path):
    stream = Stream.from_file("./data/" + file_path)
    decoder = Decoder(stream)
    messages, errors = decoder.read()

    print(errors)
    print(messages)


if __name__ == "__main__":
    parser_file("258582237_ACTIVITY.fit")
