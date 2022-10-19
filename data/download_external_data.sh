set -o errexit

curl https://markup-public-data.s3.amazonaws.com/isp/isp-inputs.tar.xz -o data/;tar -xf data/isp-input.tar.xz -C data/input/;
curl https://markup-public-data.s3.amazonaws.com/isp/isp-intermediary.tar.xz -o data/;tar -xf data/isp-intermediary.tar.xz -C data/intermediary/;
