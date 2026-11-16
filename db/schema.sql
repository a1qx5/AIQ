CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
  id                 bigserial PRIMARY KEY,
  client             text NOT NULL,
  source             text NOT NULL,
  source_path        text NOT NULL,
  document_date      date,
  source_modified_at timestamptz,
  content_hash       text,
  ingested_at        timestamptz NOT NULL DEFAULT now(),
  UNIQUE (client, source, source_path),
  UNIQUE (id, client)
);

CREATE TABLE chunks (
  id              bigserial PRIMARY KEY,
  document_id     bigint NOT NULL,
  client          text NOT NULL,
  chunk_index     integer NOT NULL,
  heading_path    text NOT NULL DEFAULT '',
  text            text NOT NULL,
  embedding       vector(1024) NOT NULL,
  embedding_model text NOT NULL,
  UNIQUE (document_id, chunk_index, embedding_model),
  FOREIGN KEY (document_id, client)
    REFERENCES documents (id, client) ON DELETE CASCADE
);

CREATE INDEX chunks_client_idx ON chunks (client);
