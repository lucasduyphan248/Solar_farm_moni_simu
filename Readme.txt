Bước 1. Cài đặt Raspberry Pi Imager tại: https://www.raspberrypi.com/software/

Bước 2. Format lại thẻ nhớ.

Bước 3. Cài đặt hệ điều hành thông qua Raspberry Pi Imager:
----------------------------------------------------------------------------------------------------------
3.1 Raspberry Pi device 	: Raspberry Pi Zero				  
3.2 Operating System    	: Raspberry Pi OS lite			  
3.3 Storage			: Chọn thẻ nhớ để ghi
3.4 Tổ hợp phím: Shift + Windows + X để tùy chỉnh cấu hình một số thông số ban đầu như: Wifi, ssh, ngôn ngữ.
3.5 Nhấn Next để tiến hành cài đặt.
----------------------------------------------------------------------------------------------------------
Bước 4. Gắn thẻ nhớ và cấp nguồn cho Raspberry Pi.
----------------------------------------------------------------------------------------------------------
Bước 5. Để cập nhật phần mềm trong Raspberry Pi OS, chạy các lệnh sau từ cửa sổ Terminal để cập nhật:
----------------------------------------------------------------------------------------------------------
sudo apt update
sudo apt full-upgrade
----------------------------------------------------------------------------------------------------------
Bước 6. Cài đặt python3 và pip chạy các lệnh sau trên cửa sổ Terminal:
----------------------------------------------------------------------------------------------------------
sudo apt install python3       	: Để cài đặt python3
python3 --version		: Kiểm tra phiên bản của python
sudo apt install git-all	: Cài đặt git
git --version			: Kiểm tra phiên bản của git
sudo apt install python3-pip	: Cài đặt pip
pip3 --version			: Kiểm tra phiên bản của pip
----------------------------------------------------------------------------------------------------------
Bước 7. Tải chương trình mô phỏng xuống:

Bước 8. Tải các thư viện cần thiết bằng cách chạy lệnh sau: 
8.1 cd gateway/
8.2 pip install -r requirement.txt
---------------------------Hoàn thành cài đặt chương trình mô phỏng---------------------------------------


Chạy chương trình mô phỏng qua lệnh: 
cd gateway/
python3 simu_modbus.py

 

	


