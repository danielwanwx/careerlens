# Jordan Lee

Fictional Senior Backend and Data Platform Engineer

## Summary

Senior software engineer with eight years of experience building backend APIs,
event-driven data services, and cloud platforms. Recently led the backend path
for an internal retrieval-backed agent used through a Teams bot. Strong in API
contracts, AWS services, distributed data systems, testing, and production
operations. No claimed experience training foundation models or operating a
hyperscale agent runtime.

## Experience

### Northstar Media, Senior Software Engineer, 2021 to present

- Designed a RESTful `invoke` API that accepts authenticated user requests,
  creates a session, routes the request through an agent service, invokes Amazon
  Bedrock, retrieves approved context from a knowledge base, and returns a
  traceable response.
- Integrated AWS Bedrock, Strands Agents, S3-backed knowledge sources, and
  DynamoDB session records behind stable service interfaces.
- Stored request status, session metadata, selected tools, and response
  references in DynamoDB. Added expiration policies for inactive sessions.
- Added unit tests for routing and service boundaries, API tests for the invoke
  endpoint, and prompt-delivery tests that verify expected context and routing.
- Moved the service from one container used for functional testing to multiple
  Docker containers after a Teams bot introduced concurrent usage. Added health
  checks and request-level logs.
- Operated a separate event platform processing 10 billion events per day with
  peak throughput of 250,000 events per second.

### Meridian Commerce, Software Engineer, 2018 to 2021

- Built Java and Python services for ingestion, validation, and delivery of
  partner data.
- Designed idempotent APIs and retry handling for asynchronous workflows.
- Participated in incident response, capacity reviews, and staged rollouts.

## Skills

Python, Java, TypeScript, REST APIs, AWS Bedrock, DynamoDB, S3, Docker, Kafka,
Spark, SQL, distributed systems, observability, unit testing, API testing

## Evidence boundaries

- The agent service was an internal production service, not a public hyperscale
  agent platform.
- Multi-container scaling is proved. Kubernetes, global scheduling, secure
  sandboxes, and cross-region failover are not claimed.
- Prompt routing tests are proved. A model evaluation platform, golden dataset,
  trace-based release gate, and online experimentation system are not claimed.
- Bedrock and knowledge-base integration are proved. Foundation-model training,
  post-training, GPU serving, and ML research are not claimed.

