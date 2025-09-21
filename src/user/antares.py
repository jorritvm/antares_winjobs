import os

class AntaresStudy:
    def __init__(self, study_path):
        self.study_path = os.path.abspath(study_path)

    def get_size_on_disk(self) -> float:
        """Return size in megabytes"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.study_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.isfile(fp):
                    total_size += os.path.getsize(fp)
        return total_size / (1024 * 1024)

    def is_output_empty(self) -> bool:
        """Check if the output folder is empty or contains only the folder 'maps'"""
        output_path = os.path.join(self.study_path, "output")
        if not os.path.exists(output_path):
            return True
        if not os.path.isdir(output_path):
            return True
        contents = os.listdir(output_path)
        if len(contents) == 0:
            return True
        if len(contents) == 1 and contents[0] == "maps":
            return True
        return False

    # static method to check if a study is a valid Antares study
    @staticmethod
    def is_valid_study(study_path):
        if not os.path.exists(study_path):
            return False

        if not os.path.isdir(study_path):
            return False

        required_files = ["input", "output", "study.antares"]
        for file in required_files:
            if not os.path.exists(os.path.join(study_path, file)):
                return False

        return True
