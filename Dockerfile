 #START FROM INSITIAL PYTHON IMAGE 
FROM python:3.12-slim

#set working directory inside container  all commands run from here 
WORKDIR /app


# copy requirements before code 
#docker caches layers
#if requirements dont change skip reinstall
#faster rebuilds only when code changes
COPY requirements_api.txt .

# install python libraries
RUN pip install --no-cache-dir -r requirements_api.txt

#copy model files 
COPY models/ ./models/

#copy apicode
COPY api/ ./api/

#tell docker which code app uses 
EXPOSE 8000

#command to run when container starts
CMD ["uvicorn","api.app:app","--host","0.0.0.0","--port","8000", "--app-dir", "/app"]
