import winsound
import loguru


class SoundUtils:
    @staticmethod
    def play_sound(sound_file: str):
        """
        Play a sound file using the winsound module.
        :param sound_file: Path to the sound file.
        """
        try:
            winsound.PlaySound(sound_file, winsound.SND_FILENAME)
        except Exception as e:
            loguru.logger.error(f"Error playing sound: {e}")

    @staticmethod
    def beep():
        """
        Play a beep sound.
        """
        try:
            winsound.Beep(1000, 500)  # Frequency: 1000 Hz, Duration: 500 ms
        except Exception as e:
            loguru.logger.error(f"Error playing beep sound: {e}")