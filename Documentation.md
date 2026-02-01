Overview
This system automates the verification of alcohol beverage labels by:
Extracting text and information from label images using GPT-4 Vision
Comparing extracted data against submitted application information
Validating the presence and accuracy of required government warning statements
Providing detailed compliance reports with pass/fail status for each field


Features
Single Label Review
Upload individual label images for verification
Enter corresponding COLA application data
Receive detailed verification results with field-by-field comparison

Batch Processing
Upload multiple label images simultaneously
CSV-format application data entry for bulk verification. This eliminates the need for one-by-one processing
Summary statistics showing approved/rejected counts
Individual results for each label in the batch


Approach and stakeholder needs addressed:
Fast response time - Optimized image preprocessing, single API call design, low-latency Azure OpenAI integration
Batch Processing - Dedicated batch tab supporting multiple simultaneous uploads with CSV application data
Simple UI - Minimal interface with straightforward buttons, drag-and-drop upload, clear visual feedback
Flexible field matching - Using AI, matching requirements are not as strict for small formatting variation except for the "GOVERNMENT WARNING," which needs to be exact
Imperfect image handling - ChatGPT-4o's model is trained to handle different image conditions and quality
Systems compliance - Purposefully uses Azure OpenAI API instead of normal the normal OpenAI API to align with existing infrastructure. This saves both time and money on two fronts: one, using normal OpenAI or other cloud-based APIs may take a very long time to get approval for FedRAMP compliance; and two, training a model from scratch would realistically take a lot of resources to do. Because the system was migrated to the Microsoft Azure platform, the Azure OpenAI API should be allowed


Technology Choices
Backend: Python/Flask - Fast development, sufficient for prototype
AI/Vision: Azure OpenAI GPT-4o - Aligns with TTB Azure infrastructure; robust vision capabilities
Image Processing: Pillow - Industry standard, handles format conversion reliably
Frontend: Vanilla HTML/CSS/JS - No build step, simple, accessible


Assumptions
English language labels only
Azure OpenAI endpoint is network-accessible
Images are standard formats (JPEG, PNG)
Single label per image
No persistent storage/database required for prototype
No authentication/authorization needed
Results do not need to integrate with COLA


Rationale Behind Design Decisions
Sequential Batch Processing: Reliability over speed for prototype. Perhaps Async with WebSockets would be future enhancement
Server-Side AI calls: Security is paramount for government applications. API keys must never reach the client
Single HTML file with embedded CSS/JS: Government networks block many domains. Avoiding npm/CDN dependencies for JS frameworks reduces potential deployment friction.