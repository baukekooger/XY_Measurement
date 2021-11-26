from dataclasses import dataclass


@dataclass
class Student:
    age: int
    name: str
    grade: int
    
    def passed(self):
        if self.grade > 5:
            print(f'{self.name} passed the test')
        else:
            print(f'{self.name} failed the test')
