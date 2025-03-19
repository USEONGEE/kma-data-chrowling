import pandas as pd


def compare_csv_files(file1: str, file2: str) -> bool:
    """
    두 CSV 파일을 읽어 DataFrame으로 변환한 후, 데이터가 완전히 동일한지 비교합니다.

    Parameters:
      - file1: 첫 번째 CSV 파일 경로
      - file2: 두 번째 CSV 파일 경로

    Returns:
      - bool: 두 파일의 데이터가 완전히 동일하면 True, 아니면 False
    """
    # CSV 파일을 읽어옵니다.
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    # DataFrame의 데이터가 완전히 동일한지 검사합니다.
    if df1.equals(df2):
        print("두 파일의 데이터는 완전히 동일합니다.")
        return True
    else:
        print("두 파일의 데이터는 동일하지 않습니다.")
        return False


# 예시 사용법:
file_path1 = "/Users/mousebook/Documents/university/연구실/오교수님/data/창운효자동_1시간기온_20250314_20250318.csv"
file_path2 = "/Users/mousebook/Downloads/20250319023706/청운효자동_1시간기온_20250314_20250318.csv"

compare_csv_files(file_path1, file_path2)
