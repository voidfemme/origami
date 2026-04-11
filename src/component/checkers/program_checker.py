from src.build_classes import ProgramDependency
import shutil


class ProgramChecker:
    @classmethod
    def get_installed_programs(
        cls, programs: list[ProgramDependency]
    ) -> list[ProgramDependency]:
        installed_programs = []
        for program in programs:
            if shutil.which(program.name):
                installed_programs.append(program)
        return installed_programs

    @classmethod
    def get_missing_programs(
        cls, programs: list[ProgramDependency]
    ) -> list[ProgramDependency]:
        missing_programs = []
        for program in programs:
            if not shutil.which(program.name):
                missing_programs.append(program)
        return missing_programs
