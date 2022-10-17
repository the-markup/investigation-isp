set -o errexit

curl https://markup-public-data.s3.amazonaws.com/isp/input.tar.xz -o data/;tar -xf data/input.tar.xz -C data/input/;
curl https://markup-public-data.s3.amazonaws.com/isp/intermediary.tar.xz -o data/;tar -xf data/intermediary.tar.xz -C data/intermediary/;