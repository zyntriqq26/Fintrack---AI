BEGIN;
CREATE TABLE  IF NOT EXISTS users(
  id SERIAL PRIMARY KEY ,
  email VARCHAR(250) NOT NULL ,
  password_hash VARCHAR(250) NOT NULL,
  full_name VARCHAR(250) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT email_uk UNIQUE(email)
);
CREATE TABLE IF NOT EXISTS transactions(
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL,
  amount NUMERIC(12,2) NOT NULL,
  transaction_type VARCHAR(20) NOT NULL,
  catagory VARCHAR(100) NOT NULL,
  description TEXT NOT NULL,
  note TEXT ,
  date DATE NOT NULL,
  time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT chk_transaction_type CHECK(transaction_type IN ( 'income','expense')),
  CONSTRAINT chk_amount CHECK(amount>0)
);
CREATE TABLE IF NOT EXISTS budget(
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL,
  catagory VARCHAR(100) NOT NULL,
  monthly_limit NUMERIC(12,2) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT  CURRENT_TIMESTAMP,
  CONSTRAINT fk_user_id_budget FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT chk_monthly_limit CHECK(monthly_limit>0),
  CONSTRAINT uk_catagory UNIQUE(user_id, catagory)

);
CREATE TABLE IF NOT EXISTS ai_chat(
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL,
  role VARCHAR(20) NOT NULL,
  message TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_user_id_ai_chat FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT chk_role CHECK(role IN('user','assistant'))

);
CREATE INDEX IF NOT EXISTS ix_transaction_fast ON transactions(user_id,date DESC);
CREATE INDEX IF NOT EXISTS ix_transaction_catageory ON transactions(user_id,catagory );
CREATE INDEX IF NOT EXISTS ix_budget ON budget(user_id);
CREATE INDEX IF NOT EXISTS ix_ai_chat ON ai_chat(user_id,created_at DESC);
COMMIT;
