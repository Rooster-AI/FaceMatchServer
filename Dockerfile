FROM python:3.9

WORKDIR .

# Install dependencies one by one for better caching
RUN pip install --no-cache-dir "git+https://github.com/Rooster-AI/rooster-deepface.git"
RUN pip install --no-cache-dir Flask==3.0.2 
RUN pip install --no-cache-dir keras==2.15.0
RUN pip install --no-cache-dir mtcnn==0.1.1
RUN pip install --no-cache-dir numpy==1.26.2
RUN pip install --no-cache-dir oauthlib==3.2.2
RUN pip install --no-cache-dir pandas==2.1.1
RUN pip install --no-cache-dir Pillow==10.1.0
RUN pip install --no-cache-dir retina-face==0.0.13
RUN pip install --no-cache-dir tqdm==4.66.1
RUN pip install --no-cache-dir supabase==2.3.4
RUN pip install --no-cache-dir python-dotenv==1.0.0
RUN pip install --no-cache-dir ultralytics
RUN pip install --no-cache-dir resend

RUN pip install opencv-python-headless
RUN pip install gunicorn

COPY facial_recognition_server facial_recognition_server
COPY main_prod.py .
COPY supabase_dao.py .
COPY models models
COPY .env .


EXPOSE 5000:5000

CMD ["sh", "-c", "python facial_recognition_server/rooster_update.py && gunicorn --workers 2 --threads 22 --worker-class=gthread --bind 0.0.0.0:5000 main_prod:app --timeout 90"]