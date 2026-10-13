# Chosen Stack

The technologies used in this project were Python and FastAPI. It appears at this time that FastAPI is a good choice for the fast creation of the API due to Pydantic's automatic validation of the data and FastAPI's ability to generate Swagger documentation, which allows us to test on the go. For storage of the data I have been using the sqlite database with SQLAlchemy. As I have experience using an ORM with models, I decided not to go into the added difficulty of debugging the PostgreSQL connection string on the local machine. This is because sqlite is zero-configuration, and the data is stored in the local directory in a.db file.

# Big Language Model (LLM) Generalization

The other key design element was separating understanding from execution. The LLM was tasked with processes requiring the sophistication of human interaction including the analysis of text, categorization and discerning if a customer was angry or abusive. But the business rules were implemented as hardcoded Python components, for example – priority boost for an angry customer or mandatory high priority for an Enterprise customer. This decision was based on the knowledge that you would not want to rely on the LLM to make strict business decisions since it is non-deterministic, whereas code will follow rules to the letter.

# Trade-offs made and i deliberately for Efficiency

A dummy for the LLM network call was added to the prototype to ensure core functionalities could be developed quickly. This prevented many hours spent debugging API latency and provisioning keys from the LLM provider, which in turn allowed me to direct efforts at testing routing, database schema, and idempotency rules. Creating a complete pytest suite was further delayed until 4/4 routes could be developed.

# The Changes I'd add before this went to production for real.

A few improvements are suggested that would be necessary for use in production: Asynchronous processing, so that no delays in the API are experienced while waiting for a response from the LLM. Tasks could be put on a Redis queue so the API can give an immediate 202 Accepted, and the LLM can run in the background. A change from a sqlite database to a PostgreSQL database, and a Docker container for easier deployment. Improvements in deduplication, using vector embeddings to find tickets that mean the same thing, with different words.

# Bonus Feature

I implemented a PII Redaction filter (redact_pii) using RegEx to strip emails and phone numbers from the ticket text before it gets sent to the LLM. In an enterprise environment, preventing data leakage to third-party AI APIs is critical. I also added a GET /stats endpoint to provide a macro-level dashboard for support managers to monitor critical backlogs and angry customer metrics.