select
    *
from read_csv("{s3_read_path}", delim = ';', header = true)