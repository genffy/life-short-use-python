import moviepy.editor as mp


def extract_audio(videos_file_path):
    my_clip = mp.VideoFileClip(videos_file_path)
    my_clip.audio.write_audiofile("./output/{get_md5(videos_file_path)}.mp3")


if __name__ == "__main__":
    files_arr = [
        "download-0.mp4",
        "download-1.mp4",
        "download-2.mp4",
        "download-3.mp4",
    ]
    for file in files_arr:
        extract_audio("./data/{file}")
