FROM matoran/lauzhack_base_learning:latest

COPY simpleSVM.py /app

RUN shuf -i 0-3000 -n 1 > random.txt

ENTRYPOINT [ "python", "simpleSVM.py" ]