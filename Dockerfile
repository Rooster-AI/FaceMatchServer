FROM python:3.9

WORKDIR .

# Install cron
RUN apt-get update && apt-get install -y cron

# Install dependencies one by one for better caching
RUN pip install --no-cache-dir "git+https://github.com/Rooster-AI/rooster-deepface.git"
RUN pip install --no-cache-dir Flask==3.0.2 
RUN pip install --no-cache-dir tensorflow==2.9.0
RUN pip install --no-cache-dir tensorflow-addons
RUN pip install --no-cache-dir mtcnn==0.1.1
RUN pip install --no-cache-dir numpy==1.26.2
RUN pip install --no-cache-dir oauthlib==3.2.2
RUN pip install --no-cache-dir pandas==2.1.1
RUN pip install --no-cache-dir Pillow==10.1.0
RUN pip install --no-cache-dir retina-face==0.0.13
RUN pip install --no-cache-dir tqdm==4.66.1
RUN pip install --no-cache-dir supabase==2.3.4
RUN pip install --no-cache-dir python-dotenv==1.0.0
RUN pip install --no-cache-dir resend

RUN pip install opencv-python-headless
RUN pip install gunicorn

COPY facial_recognition_server facial_recognition_server
COPY main_prod.py .
COPY supabase_dao.py .
COPY models models
COPY .env .
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod +x /usr/local/bin/entrypoint.sh

# Copy cron file to the cron.d directory on container
COPY cron /etc/cron.d/cron

# Give execution access
RUN chmod 0644 /etc/cron.d/cron

# Run cron job on cron file
RUN crontab /etc/cron.d/cron

# Create the log file
RUN touch /var/log/cron.log

EXPOSE 5000:5000

CMD cron && gunicorn --workers 2 --threads 22 --worker-class=gthread --bind 0.0.0.0:5000 main_prod:app --timeout 90 && tail -f /var/log/cron.log