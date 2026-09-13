FROM manimcommunity/manim:v0.21.0

USER root

WORKDIR /app

COPY pyproject.toml ./

RUN pip install \
    langchain \
    langchain-google-genai \
    langchain-mcp-adapters \
    langchain-openai \
    python-dotenv \
    streamlit \
    fastmcp

COPY . .

EXPOSE 8501

CMD ["sh", "-c", "streamlit run client1.py --server.address=0.0.0.0 --server.port=${PORT:-8501}"]