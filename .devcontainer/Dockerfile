FROM public.ecr.aws/aws-mde/universal-image:1.0
COPY requirements-dev.txt .
COPY .bash_profile .
COPY .bashrc .
RUN pip3.10 install --upgrade pip && \
    pip3.10 install -r requirements-dev.txt && \
    sudo ln -sf  /usr/share/zoneinfo/Asia/Tokyo /etc/localtime && \
    sudo cp .bash_profile ~/.bash_profile && \
    sudo cp .bashrc ~/.bashrc && \
    npm install -g aws-cdk
RUN npm install -g @go-task/cli
