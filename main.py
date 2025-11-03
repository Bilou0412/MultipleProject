from app.file_manager import JobOpening,Cv



def main():
    cv = Cv("data/input/cv.pdf")
    job_opening = JobOpening("data/input/JO.pdf")

if __name__ == "__main__":
    main()