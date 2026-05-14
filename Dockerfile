# Use an official Python runtime as a parent image
FROM python:3.9-slim

# 更新套件清單並安裝基礎工具
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    unixodbc-dev \
    g++ \
    && rm -rf /var/lib/apt/lists/* 
# 2. 下載金鑰並存放到專門的 keyring 資料夾，同時加入來源清單
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft-archive-keyring.gpg \
    && echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-archive-keyring.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list

# 3. 安裝 ODBC Driver 17
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17

#set the working directory in the container
WORKDIR /app    

#generate the requirements.txt file
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#copy the codes
COPY . .

#enable streamlit default port 8501
EXPOSE 8501

#execute the instructions
CMD ["streamlit", "run", "analyze_singleerack.py", "--server.port=8501", "--server.address=0.0.0.0"]