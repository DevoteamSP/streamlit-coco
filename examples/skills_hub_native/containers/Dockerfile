# Build context (made by build_and_push.sh):
#   streamlit_coco_pkg/  the library, from this repository
#   app/                 examples/skills_hub (app.py, shop/, samples/)
#   requirements.txt
FROM python:3.11-slim AS builder
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY streamlit_coco_pkg/ /tmp/streamlit_coco_pkg/
RUN pip install --no-cache-dir /tmp/streamlit_coco_pkg/ && rm -rf /tmp/streamlit_coco_pkg/

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY app/ .
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
EXPOSE 8501
# Publish the bundled skills to the application's stage, optionally probe the Agent API (the result
# goes to the logs), then serve. A failed step is logged and the page still starts: it says what is
# wrong.
ENTRYPOINT ["/bin/sh", "-c", "python -m shop.bootstrap || echo 'bootstrap failed'; if [ \"$SKILLS_HUB_PROBE\" = \"1\" ]; then python -m shop.probe || echo 'probe failed'; fi; exec streamlit run app.py --server.port=8501 --server.address=0.0.0.0"]
