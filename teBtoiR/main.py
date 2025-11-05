from app.file_manager import JobOpening,Cv



def main():
    cv = Cv("data/input/CV.pdf")
    job_opening = JobOpening("data/input/FP.pdf")
    cv.get_raw_data()
    job_opening.get_raw_data()
    print(f"-----------\n{cv.raw_data}\n-----------")
    print(f"-----------\n{job_opening.raw_data}\n-----------")
if __name__ == "__main__":
    main()