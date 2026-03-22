## Terms of Service

### 1. Acceptance of Terms

By inviting and using this Discord bot ("NoScam"), you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use the Bot.

### 2. Description of Service

The Bot provides automated scam detection services for Discord servers, including:
- Image hash-based scam detection
- Automated moderation actions
- Hash management and reporting
- Server-specific configuration options

### 3. User Responsibilities

Server administrators are responsible for:
- Configuring the Bot appropriately for their server
- Reviewing and managing false positives
- Ensuring the Bot's actions align with their server rules
- Monitoring the Bot's performance and reporting issues

### 4. Limitations and Disclaimers

- The Bot is provided "as is" without warranties of any kind
- We do not guarantee 100% accuracy in scam detection
- False positives and false negatives may occur
- The Bot may experience downtime or service interruptions
- We are not responsible for any damages resulting from the use of the Bot

### 5. Prohibited Use

You may not:
- Attempt to bypass or manipulate the Bot's detection systems
- Use the Bot for malicious purposes
- Overload the Bot with excessive requests

### 6. Modifications to Service

We reserve the right to:
- Modify or discontinue the Bot at any time
- Update these Terms of Service
- Change features or functionality
- Restrict access to the Bot

### 7. Termination

We may terminate or suspend access to the Bot immediately, without prior notice, for any reason, including breach of these Terms.

---

## Privacy Policy

### 1. Information We Collect

The Bot collects and stores the following information:

**Server Information:**
- Server ID (guild ID)
- Channel IDs for reporting
- Server configuration settings

**User Information:**
- User IDs of users who post detected scam images
- Detection timestamps

**Content Information:**
- Image hashes (perceptual hashes of images, not the actual images)
- Detection statistics

### 2. How We Use Information

We use collected information to:
- Detect and prevent scam content
- Provide moderation services
- Generate statistics and reports

### 3. Data Storage

- All data is stored in a local SQLite database
- Image hashes are stored, but actual images are never saved
- Server configurations are stored per-server basis
- Detection logs are maintained for statistical purposes

### 4. Data Sharing

We do NOT:
- Share your data with third parties
- Sell your data
- Use your data for advertising
- Transfer data outside the Bot's operation

Global hash database may be shared across servers to improve scam detection, but this only includes image hashes and descriptions, not user or server-specific information.

### 5. Data Retention

- Server configurations are retained while the Bot is active in your server
- Detection logs are retained indefinitely for statistical purposes
- Upon removing the Bot from your server, you may request data deletion

### 6. User Rights

Server administrators have the right to:
- Request a copy of their server's data (via `/export_hashes`)
- Request deletion of their server's data
- Opt-out of global hash usage (via `/config use_global_hashes`)
- Manage false positives

### 7. Security

We implement reasonable security measures to protect stored data:
- Local database storage
- Access restricted to Bot operations
- No external data transmission except Discord API interactions

### 8. Changes to Privacy Policy

We may update this Privacy Policy from time to time. Continued use of the Bot after changes constitutes acceptance of the updated policy.