# **CHAPTER ONE**

# **INTRODUCTION**

## **1.1 Background of Study**

Pharmaceutical products are inherently time-limited: every drug is manufactured with a defined shelf life, after which its chemical composition can no longer be guaranteed to be safe or effective, and beyond which continued use may expose patients to reduced therapeutic benefit or outright harm (Rajalakshmi et al., 2024). Ensuring that expired products are identified and removed from circulation before they reach a patient is therefore a foundational responsibility of pharmacy practice, whether in a hospital dispensary, a community pharmacy, or a wholesale distribution warehouse.

Historically, this responsibility has been discharged through manual stock-checking, in which pharmacy staff periodically inspect shelves, ledgers, or spreadsheets to identify products approaching their expiry date (Friday & Sorlihu, 2025). While adequate for very small inventories, manual tracking becomes increasingly unreliable as the number of stock-keeping units grows, since human attention is finite and easily diverted by the routine pressures of dispensing, procurement, and patient service. Jaju et al. (2023), in a cross-sectional investigation of a newly established institutional pharmacy in Eastern India, found that medication expiry was one of the three most frequently recurring inventory problems, alongside stockouts and supplier-related issues, underscoring that expiry management remains a live operational challenge rather than a solved one, even in relatively well-resourced institutional settings.

The last decade has seen growing interest in automating this process. Simple rule-based systems that compare a stored expiry date against the current date and issue an alert once a threshold is reached, typically thirty days, have been proposed and implemented with reported success in reducing the manual burden on staff (Friday & Sorlihu, 2025). More technically ambitious systems have layered machine learning models, such as Random Forest classifiers and ARIMA or LSTM time-series forecasters, on top of this basic logic, primarily to support demand forecasting rather than to improve expiry detection itself (International Journal of Research Publication and Reviews \[IJRPR\], 2025). At the same time, systematic evidence continues to accumulate that automation of pharmacy processes in general, not only expiry alerts, measurably reduces medication errors when compared with traditional manual systems (Shbaily et al., 2025).

However, a closer reading of this body of work reveals that existing systems tend to treat all pharmaceutical products alike, applying a single fixed alert threshold regardless of a drug's cost, criticality, or turnover rate, and relying on a single notification channel that research on clinical notifications suggests is frequently ineffective on its own (PMC, 2025). Furthermore, studies of real-world pharmacy practice indicate that many practising pharmacists are not formally trained in structured inventory-classification techniques such as ABC or VED analysis, meaning that any system intended for practical adoption cannot assume specialist knowledge on the part of its users (Journal of Community Pharmacy Practice, 2024). It is against this background, a well-documented problem, a partially automated but still incomplete set of existing solutions, and a body of end-user research pointing to specific, addressable gaps, that this project is situated.

## **1.2 Problem Statement**

Despite the range of expiry-management tools reviewed in the literature, pharmacies, particularly small and medium-sized community pharmacies, continue to experience losses arising from expired stock, alongside the associated risks of dispensing expired medication to patients (Jaju et al., 2023). The core deficiencies identified in existing systems can be summarised as follows:

First, most existing expiry-detection systems apply a single, fixed alert threshold uniformly across all drug types, without regard for differences in cost, criticality, or how quickly a given category of drug typically moves through inventory (Friday & Sorlihu, 2025). Second, the dominant notification method in existing systems is a single channel, usually electronic mail, despite evidence that passive, one-time notifications of this kind are frequently ignored; in one study of clinical notifications, fewer than one-quarter led to any recorded action within a week (PMC, 2025). Third, where more sophisticated analytical techniques have been introduced, such as machine learning-based demand forecasting, the added sophistication has been directed at sales prediction rather than at the expiry-detection and alerting process itself, leaving the central problem only partially addressed (IJRPR, 2025). Fourth, no reviewed system provides a mechanism by which staff can acknowledge an alert and record the corrective action taken, meaning that existing tools cannot demonstrate, for audit or regulatory purposes, that a warning was actually acted upon. Finally, existing systems generally assume a level of formal inventory-management knowledge that real-world pharmacy staff often do not possess (Journal of Community Pharmacy Practice, 2024), creating a mismatch between system design and the practical realities of pharmacy operation.

This project addresses these deficiencies by developing a product expiry alert management system that classifies pharmaceutical stock by value and criticality, applies category-appropriate alert lead-times, delivers alerts through multiple channels with escalation for unacknowledged warnings, and records the resolution of each alert, all within an interface usable by staff without specialised inventory-management training.

## **1.3 Motivation**

The motivation for this project is both practical and academic. On the practical side, the continued loss of pharmaceutical stock to expiry, and the associated risk of expired medication reaching patients, represents a tangible, recurring cost to healthcare providers and a patient-safety concern that automation is well placed to mitigate (Shbaily et al., 2025). Community and small institutional pharmacies, which often operate with limited staff and no dedicated inventory specialists, stand to benefit disproportionately from a system that does not require prior expertise in formal stock-classification methods (Journal of Community Pharmacy Practice, 2024).

On the academic side, the review of existing literature revealed a consistent pattern: systems either address expiry detection using simple, undifferentiated logic, or introduce genuine technical sophistication in a part of the problem, demand forecasting, that is adjacent to, rather than central to, expiry management. This gap presented an opportunity to make a targeted, well-defined technical contribution: embedding a classification model directly into the alerting logic of a working system, rather than treating classification as a separate analytical exercise, as has been the case in prior studies (Jaju et al., 2023). The prospect of contributing a system that is both practically deployable and technically distinct from what already exists provided the motivation to pursue this specific topic rather than a more generic pharmacy management system.

## **1.4 Aim and Objectives**

The aim of this project is to design and implement a product expiry alert management system for pharmacies that improves on existing approaches by combining category-based alert thresholds, multi-channel escalating notifications, and closed-loop action tracking within a single, usable system.

The specific objectives of the study are to:

i. Review existing expiry-alert and pharmacy-management systems in order to identify their technical and practical limitations;

ii. Design a classification mechanism, informed by Always Better Control (ABC) and Vital-Essential-Desirable (VED) analysis, that automatically determines an appropriate alert lead-time for each drug category;

iii. Implement a rule-based expiry-detection engine that applies these category-specific thresholds rather than a single fixed rule;

iv. Implement a multi-channel notification mechanism, combining electronic mail and short message service (SMS), with an escalation procedure for alerts that remain unacknowledged after a defined period;

v. Implement an action-tracking feature that allows pharmacy staff to record the resolution of each alert, thereby creating an auditable record of corrective action;

## **1.5 Research Methodology**

This project adopts Object-Oriented Analysis and Design Methodology (OOADM), applied iteratively. OOADM was selected because the system's requirements, while clearly defined, benefit from being expressed and communicated through visual models, including use case diagrams to represent the interactions of Administrator, Pharmacist, and Supervisor roles, entity relationship diagrams to represent the underlying data structures, and sequence diagrams to represent the alert-escalation workflow. The iterative delivery approach allows the system to be built and tested in stages, beginning with core drug-record management, followed by the classification and expiry-detection logic, then the multi-channel notification and escalation mechanism, and finally the action-tracking and reporting features. This staged approach reduces risk and allows each component to be verified before the next is layered on top of it.

## **1.6 Scope of Study**

This project is limited to the design and implementation of a software system for tracking pharmaceutical stock and generating expiry alerts within a single pharmacy or small group of affiliated pharmacies. The system covers drug record management, automatic classification by value and criticality, category-based expiry detection, multi-channel notification with escalation, and action-tracking for alert resolution.

The project does not extend to full point-of-sale functionality, prescription management, or integration with national pharmaceutical regulatory databases, as these fall outside the defined problem of expiry-alert management. Similarly, while a lightweight, optional predictive component may be included to flag drugs unlikely to sell before expiry, the system does not implement the more data-intensive forecasting techniques, such as deep reinforcement learning-based inventory optimisation, that have been explored in the wider research literature, as these require historical datasets and computational resources beyond the scope of a single institution's typical pharmacy operations.

## **1.7 Significance of Study**

This study is significant at three levels. First, at the practical level, it provides pharmacies, particularly small and medium-sized ones without dedicated inventory-management expertise, with a usable tool for reducing losses associated with expired stock and the associated patient-safety risk (Jaju et al., 2023; Rajalakshmi et al., 2024). Second, at the technical level, it contributes an implementation in which a multi-criteria classification technique (ABC/VED analysis) is embedded directly into the operational logic of a working alert system, rather than being used only as an offline diagnostic tool, addressing a gap identified across the reviewed literature. Third, at the academic level, the project demonstrates that meaningful technical contribution in this problem domain does not require adopting the heaviest available machine learning techniques; a carefully designed rule-based and classification-driven system, supplemented where appropriate by lightweight predictive modelling, can address the actual gaps identified in prior work more directly than the addition of complex forecasting models that leave the core expiry-detection logic unchanged (IJRPR, 2025).

## **1.8 Definition of Terms**

**Expiry Date**: The date, determined by the manufacturer, after which a pharmaceutical product is no longer guaranteed to be safe or fully effective for use.

**ABC Analysis**: An inventory classification technique that ranks items by their consumption value (unit cost multiplied by quantity used), typically grouping them into tiers A, B, and C in descending order of value.

**VED Analysis**: An inventory classification technique that ranks items by clinical criticality, categorising them as Vital, Essential, or Desirable.

**ABC-VED Matrix**: A combined classification technique that cross-references the value-based ABC categories with the criticality-based VED categories to determine the overall priority of an item for inventory control.

**Alert Threshold (Lead-Time):** The number of days before a product's expiry date at which the system is configured to generate a warning notification.

**Escalation**: The automated process by which an unacknowledged alert is either resent or forwarded to a different recipient, such as a supervisor, after a defined period has elapsed.

**Closed-Loop Tracking**: A design feature in which an alert is not considered complete until a staff member has recorded the action taken in response to it, creating an auditable record.

**Multi-Channel Notification**: The delivery of a single alert through more than one communication medium, such as electronic mail and SMS, to increase the likelihood that it is seen and acted upon.

**Rule-Based System**: A software component whose behaviour is governed by a defined set of conditional rules, as distinct from a system that learns its behaviour from data.

# **CHAPTER TWO** 

# **LITERATURE REVIEW**

## **2.1 Concept of Pharmaceutical Inventory and Expiry Management**

Pharmaceutical inventory management refers to the set of practices by which healthcare facilities and pharmacies control the ordering, storage, monitoring, and disposal of drug stock so as to balance product availability against cost, wastage, and patient safety. Expiry management is one specific concern within this broader field: the process of ensuring that pharmaceutical products are identified, flagged, and removed from circulation before their manufacturer-assigned shelf-life elapses (Jaju et al., 2023). Because pharmaceuticals are perishable in a way that many other retail goods are not, expiry management carries consequences beyond ordinary stock loss; the use of an expired product can result in reduced therapeutic effect or direct harm to a patient (Rajalakshmi et al., 2024).

### ***2.1.1 Traditional (Manual) vs. Automated Inventory Management***

Traditional inventory management in pharmacies has historically relied on manual stock cards, ledgers, or spreadsheets, in which pharmacy staff periodically record quantities received, dispensed, and remaining, alongside relevant dates such as manufacture and expiry (Jaju et al., 2023). This approach depends heavily on the diligence and availability of staff, and becomes progressively less reliable as the number of distinct products held in stock increases. Automated inventory management, by contrast, uses a centralised database and, in more developed implementations, barcode or QR-code scanning to capture and update stock information without requiring manual transcription (Friday & Sorlihu, 2025). Comparative evidence indicates that automation is associated with a moderately positive overall effect on pharmacy operations relative to traditional manual systems, particularly in reducing the incidence of medication errors (Shbaily et al., 2025).

### ***2.1.2 Expiry Management as a Subset of Inventory Control***

Within the wider discipline of inventory control, expiry management is best understood as a specialised concern that intersects with, but is not identical to, stock-level management. A pharmacy may hold an adequate quantity of a given drug and still suffer losses if that stock is not rotated or monitored for approaching expiry (Jaju et al., 2023). Techniques developed for general inventory control, including turnover analysis and classification by consumption value, can be adapted for this purpose, but expiry management additionally requires date-specific monitoring that general stock-level tools do not always provide. Studies of real pharmacy operations have found that expiry of medication is consistently among the most frequently cited operational problems, alongside stockouts and supplier-related issues (Jaju et al., 2023), indicating that this subset of inventory control deserves dedicated attention rather than being treated as an incidental by-product of stock management.

## **2.2 The Role of Technology in Pharmacy Management**

Technology has progressively reshaped pharmacy management from a paper-based, human-dependent activity into one supported, and increasingly driven, by software systems. This shift has touched dispensing, procurement, patient records, and, of direct relevance to this project, the monitoring of stock condition and expiry (Shbaily et al., 2025).

### ***2.2.1 Pharmacy Practice in the Digital Age***

The digitisation of pharmacy practice has introduced centralised databases capable of holding structured records for every item in stock, replacing the fragmented paper records of earlier practice (Friday & Sorlihu, 2025). Systems of this kind typically use a relational database management system, such as MySQL, to store fields including drug name, batch number, manufacturing date, expiry date, and quantity, allowing staff to query and update records far more quickly than manual methods permit. A study of pharmaceutical logistics management demonstrated that digitising procurement, distribution, and reporting functions within a single web-based system reduced manual data-entry errors and shortened the time required to generate operational reports (Brilliance: Research of Artificial Intelligence, 2025).

### ***2.2.2 Role of Automation in Pharmaceutical Inventory***

Automation extends digitisation by allowing routine monitoring tasks, such as checking whether any item is approaching its expiry date, to be performed by the system itself rather than by a member of staff. Friday and Sorlihu (2025) describe a system in which an algorithm runs periodically, comparing the current date against every stored expiry date and generating an alert once a defined threshold is reached, without requiring a member of staff to initiate the check. A systematic review of pharmacy automation more broadly found that automated dispensing systems and computerised order entry significantly reduced medication errors relative to manual processes, based on a synthesis of 32 studies drawn from an initial pool of 1,085 (Shbaily et al., 2025).

### ***2.2.3 Role of Artificial Intelligence in Pharmacy Systems***

Beyond straightforward automation, some recent systems incorporate machine learning techniques to support pharmacy operations. The International Journal of Research Publication and Reviews (2025) describes a system that combines a rule-based expiry check with Random Forest and Logistic Regression classifiers, alongside ARIMA and LSTM time-series models, to forecast seasonal demand for stock planning purposes. It is notable, however, that in this design the artificial intelligence components are applied to demand forecasting rather than to the expiry-detection process itself, which remains governed by a simple threshold rule (International Journal of Research Publication and Reviews, 2025). This distinction, between where intelligence is applied and where the core problem actually lies, is discussed further in section 2.4.2.

## **2.3 Inventory Classification Models**

A recurring theme in the literature on pharmaceutical inventory is the use of classification models to determine which items warrant closer monitoring and control. Two models, ABC analysis and VED analysis, dominate this literature and form a central technical basis for this project.

### ***2.3.1 History and Evolution of ABC Analysis***

ABC analysis, sometimes expanded as “Always Better Control,” is rooted in the Pareto Principle, an observation attributed to the Italian economist Vilfredo Pareto in the late nineteenth century that a small proportion of causes tends to account for a disproportionately large share of overall effect (MRPeasy, 2025). This principle was later formalised into a business inventory-classification technique, generally credited to General Electric in the 1950s, in which stock items are ranked by their annual consumption value, calculated as demand multiplied by unit cost, and grouped into three tiers, A, B, and C, in descending order of value (NetSuite, 2023). Applied to pharmaceuticals, ABC analysis has been used to identify a small number of high-value drugs that account for a large share of total pharmaceutical expenditure, allowing institutions to prioritise monitoring resources accordingly (Mfizi et al., 2023).

### ***2.3.2 VED (Vital-Essential-Desirable) Analysis***

Where ABC analysis classifies items purely by financial value, VED analysis classifies items by clinical criticality, grouping drugs into Vital, Essential, and Desirable categories based on the consequence of their unavailability to patient care (Jaju et al., 2023). A drug of low financial value may nonetheless be clinically vital, meaning that value-based classification alone can understate its importance; VED analysis is intended to correct for this by introducing a criticality dimension independent of cost. Studies applying VED analysis in pharmaceutical settings have used it to identify products that, despite representing a small share of expenditure, require stringent stock control because a shortage would directly endanger patient care (Mfizi et al., 2023).

### ***2.3.3 The ABC-VED Matrix***

Because ABC and VED analysis classify items along different dimensions, cost and criticality respectively, several studies have combined the two into a single ABC-VED matrix, cross-referencing an item's value tier against its criticality tier to arrive at an overall control priority (Jaju et al., 2023). In a cross-sectional analysis of an institutional pharmacy in Eastern India, Jaju et al. (2023) applied ABC, VED, and the combined ABC-VED matrix to a full year of dispensing data and used the resulting classification to recommend which drug categories required the most stringent monitoring. Similarly, an ABC-VEN analysis (VEN being a regionally common variant of VED) conducted on 457 pharmaceutical items in Rwanda found that a small subset of products classified in the highest value category accounted for the large majority of total pharmaceutical cost, supporting the case for differentiated monitoring by category rather than uniform treatment of all stock (Mfizi et al., 2023).

### ***2.3.4 Limitations of Classification Models in Practice***

Despite their analytical value, ABC and VED analysis have, in the reviewed literature, been applied almost exclusively as offline research tools rather than as components embedded within operational software. Jaju et al. (2023) and Mfizi et al. (2023) both use these techniques to analyse historical dispensing data and produce recommendations, but neither study describes a working system in which the classification automatically determines system behaviour, such as an alert threshold. A further limitation, identified in a pilot study of community pharmacists, is that a majority of practising pharmacists are not familiar with formal inventory-classification techniques such as ABC, VED, or FSN (Fast-, Slow-, Non-moving) analysis, meaning that any system relying on staff to manually apply these techniques is unlikely to be used correctly, or at all, in ordinary practice (Journal of Community Pharmacy Practice, 2024).

## **2.4 Expiry Detection and Alerting Systems**

Expiry detection and alerting systems form the technical core of the problem area addressed by this project. The reviewed literature includes systems that vary considerably in the sophistication of their detection logic and the channels used to deliver alerts.

### ***2.4.1 Rule-Based Detection Algorithms***

The most common approach to expiry detection identified in the literature is a rule-based algorithm that periodically compares the current system date to each stored expiry date and flags any item falling within a predefined threshold, typically thirty days (Friday & Sorlihu, 2025). Goyal et al. (2022) similarly rely on stored date fields, though their contribution is focused on recovering expiry information via optical character recognition rather than on the alerting logic itself. Rule-based detection of this kind is computationally simple and easy to verify, but the reviewed systems apply a single fixed threshold uniformly across all products, without differentiating between drug categories of differing cost or clinical criticality (Friday & Sorlihu, 2025).

### ***2.4.2 Machine Learning-Based Forecasting in Expiry Systems***

A smaller number of systems extend rule-based detection with machine learning components, though, as noted in section 2.2.3, this additional sophistication has generally been directed at demand forecasting rather than expiry detection itself (International Journal of Research Publication and Reviews, 2025). At a more advanced level again, research published on arXiv has explored deep reinforcement learning approaches to inventory replenishment for perishable pharmaceutical products under non-stationary demand, comparing learned policies against classical base-stock inventory models (arXiv, 2025\) and proposing hybrid rule-based and reinforcement-learning approaches for dynamic replenishment (arXiv, 2026). While these approaches represent genuine algorithmic advances in perishable-inventory theory, their data and computational requirements place them beyond the practical reach of a typical small or medium pharmacy, and beyond the scope of an implementation of this kind.

### ***2.4.3 Barcode/QR-Based Data Capture***

A recurring design feature across the more developed expiry-alert systems is the use of barcode or QR-code scanning to capture stock information at the point of receipt, reducing the manual data-entry errors associated with typed input (Friday & Sorlihu, 2025). Goyal et al. (2022) extend this idea further by proposing optical character recognition as a means of recovering expiry information directly from a product's packaging in cases where the printed label has been damaged or is no longer legible, addressing a specific failure mode that barcode scanning alone does not solve. Both approaches share the underlying goal of reducing reliance on manual, error-prone data entry at the point where stock information first enters the system.

## **2.5 Notification and Escalation Technology**

Detecting an approaching expiry date is only useful if the resulting alert reaches, and prompts action from, the relevant member of staff. The literature on notification technology, much of it drawn from adjacent clinical contexts, provides useful evidence on how alerts should be delivered and followed up.

### ***2.5.1 Email-Based Notification Systems***

Electronic mail is the dominant notification channel among the expiry-alert systems reviewed. Friday and Sorlihu (2025) implement an SMTP-based mechanism that automatically generates an email containing drug name, batch number, and expiry date once an item is flagged by the detection algorithm, sending it to pharmacists, healthcare providers, and inventory managers. Testing of this mechanism in a controlled environment found that email alerts were delivered promptly and reliably, and user feedback reported improved efficiency relative to manual tracking (Friday & Sorlihu, 2025). The same study, however, identifies the expansion of notification methods beyond email as a direction for future improvement, implicitly acknowledging the limitation of relying on a single channel.

### ***2.5.2 SMS and Multi-Channel Alerting***

A smaller number of systems extend notification beyond email to include short message service (SMS) alongside email, and combine this with a colour-coded dashboard to communicate urgency (International Journal of Research Publication and Reviews, 2025). Commercial solutions have gone further still, describing tiered alert lead-times that vary by product category, for example longer warning periods for high-value biologics than for fast-moving generic drugs, together with an audit log intended to support regulatory compliance (Remindax, 2026). While instructive as a design pattern, this particular source describes a proprietary commercial product rather than a peer-reviewed research contribution, and no underlying algorithm or evaluation data is disclosed.

### ***2.5.3 Escalation and Closed-Loop Acknowledgment Models***

Evidence from an adjacent clinical context indicates that a single, passive notification is often insufficient to prompt action. A study of asynchronous, non-interruptive electronic health record notifications, in which 388 alerts concerning potentially inappropriate prescriptions were routed to either a prescribing clinician or a pharmacist, found that only 23.2 percent of notifications led to a prescription change within seven days, with no significant difference between the two routing conditions (PMC, 2025). This finding suggests that escalation, resending an alert or forwarding it to an additional recipient after a defined period without acknowledgment, may be necessary to achieve reliable follow-through, a feature that none of the pharmacy-specific expiry-alert systems reviewed in this chapter currently implement.

## **2.6 Pharmacy Staff and System Usability**

The effectiveness of any expiry-alert system ultimately depends on whether the staff who use it can and do interact with it correctly. This section considers the human side of the system, distinct from its underlying technical architecture.

### ***2.6.1 Human-Computer Interaction in Pharmacy Software***

Human-computer interaction in the pharmacy context concerns how staff perceive, interpret, and act upon information presented by a system. Dashboard-style interfaces, such as the colour-coded severity view described by the International Journal of Research Publication and Reviews (2025), aim to reduce the cognitive effort required to interpret system output by translating raw date data into a visual indicator of urgency. Similarly, an indexed dashboard interface developed for tracking chronic drug claims at a hospital pharmacy improved staff visibility into claim status and reduced the time spent locating records, illustrating the general value of well-designed status displays in pharmacy software (Indonesian Journal of Global Health Research, 2025), even though that particular system was not concerned with expiry management.

### ***2.6.2 Usability for Non-Specialist Users***

A pilot study examining the knowledge, practice, and challenges of pharmaceutical inventory management among community pharmacists found that most respondents managed stock based on experience rather than any formal method, and that approximately seventy percent were unaware of standard inventory-classification techniques such as ABC, VED, or FSN analysis (Journal of Community Pharmacy Practice, 2024). This finding has direct design implications: a system that assumes familiarity with these techniques, for example by requiring staff to manually assign a VED category before an alert threshold can be set, is unlikely to be used correctly by its intended audience. It follows that any classification logic embedded in a system of this kind should operate automatically in the background, presenting staff only with the resulting alert and its urgency, rather than requiring them to perform or understand the underlying classification themselves.

## **2.7 Enabling Technologies for This Project**

Having reviewed the relevant concepts, models, and prior systems, this section identifies the specific technologies selected for the implementation of the present project and the rationale for each choice, drawn from the strengths and limitations observed in the systems reviewed above.

### ***2.7.1 Backend Architecture (Node.js/Express)***

A Node.js runtime with the Express framework is adopted for the system's backend, in preference to the PHP-based backends used in some reviewed systems (Brilliance: Research of Artificial Intelligence, 2025). Node.js provides native support for asynchronous, event-driven processing, which is required for the scheduled background checks and API-based notification dispatch described in sections 2.4.1 and 2.5.2, and integrates more directly with the scheduled-job and external API libraries discussed below.

### ***2.7.2 React and Tailwind CSS for the Dashboard***

The system's front-end dashboard is implemented using React with Tailwind CSS, following the approach used by the International Journal of Research Publication and Reviews (2025) system, whose colour-coded severity dashboard was found to give staff a clearer, faster view of near-expiry stock than a plain tabular list. This choice is consistent with the usability requirement identified in section 2.6.2, since a well-designed visual dashboard reduces the interpretive burden placed on staff without formal inventory-management training.

### ***2.7.3 Relational Database Design (MySQL/PostgreSQL)***

A relational database, either MySQL or PostgreSQL, is used to store drug records, alert history, and user accounts, following the general pattern established by Friday and Sorlihu (2025), whose MySQL-based schema for drug, batch, pharmacy, supplier, user, and alert tables demonstrated that a relational structure is well suited to the record-keeping and querying demands of an expiry-alert system. PostgreSQL is considered as an alternative where more complex audit-log querying is required, since its handling of structured, related audit data is generally considered more robust for this purpose, though either choice is compatible with the system's overall design.

### ***2.7.4 Multi-Channel APIs (Twilio, SendGrid)***

To address the single-channel limitation identified in section 2.5.1, the system integrates the Twilio API for SMS delivery alongside SendGrid or an equivalent SMTP-based service for email, rather than relying on email alone as in Friday and Sorlihu (2025). This directly responds to the evidence, discussed in section 2.5.3, that single, passive notifications frequently fail to prompt timely action (PMC, 2025), and supports the escalation mechanism central to this project's contribution.

### ***2.7.5 Scheduled Job Processing (node-cron)***

Finally, the periodic expiry-detection check and the escalation logic for unacknowledged alerts are implemented using node-cron, a scheduling library that allows tasks to run automatically at defined intervals without requiring a user to be logged in. This mirrors the daily scheduled check described by Friday and Sorlihu (2025), implemented in their case using a cron job to run a Python-based detection script, and extends it to additionally manage the escalation timing central to the closed-loop design introduced in section 2.5.3.

# **Literature Review Table**

## **References**

arXiv. (2025). Classical and deep reinforcement learning inventory control policies for pharmaceutical supply chains with perishability and non-stationarity. arXiv preprint.

arXiv. (2026). Learning to replenish: A hybrid deep reinforcement learning approach for dynamic inventory management in pharmaceutical supply chains. arXiv preprint.

Brilliance: Research of Artificial Intelligence. (2025). Web-based system design and implementation for optimizing pharmaceutical logistics management. Brilliance: Research of Artificial Intelligence.

Friday, E. A., & Sorlihu, T. O. (2025). Automated drug expiry detection and alert system via email notifications. American Journal of Networks and Communications, 14(1), 1–9. https://doi.org/10.11648/j.ajnc.20251401.11

Goyal, P., Goyal, N., Singh, P., Mittal, N., Jindal, N., & Kaur, K. (2022). Pharmaceutical drugs expiry date tracking: A visionary approach. Concurrency and Computation: Practice and Experience, 34(28), Article e7358. https://doi.org/10.1002/cpe.7358

Indonesian Journal of Global Health Research. (2025). Development of a web-based chronic drug claims management system. Indonesian Journal of Global Health Research.

International Journal of Research Publication and Reviews. (2025). Smart pharmacy management system with AI-based expiry detection. International Journal of Research Publication and Reviews, 6(8), 4746–4752.

Jaju, R., Varshney, S., Gupta, P., Bihani, P., & Karim, H. M. R. (2023). Inventory control mechanism of the pharmacy store of a recently established national institute in Eastern India: A cross-sectional, investigative analysis. Cureus, 15(11), Article e49632. https://doi.org/10.7759/cureus.49632

Journal of Community Pharmacy Practice. (2024). A pilot study on knowledge, practice, and challenges of pharmaceutical inventory management among community pharmacists. Journal of Community Pharmacy Practice.

Mfizi, E., Niragire, F., Bizimana, T., & Mukanyangezi, M. F. (2023). Analysis of pharmaceutical inventory management based on ABC-VEN analysis in Rwanda: A case study of Nyamagabe district. Journal of Pharmaceutical Policy and Practice, 16(1), Article 30\. https://doi.org/10.1186/s40545-023-00540-5

MRPeasy. (2025). ABC analysis (80/20 rule) in inventory management. MRPeasy. https://www.mrpeasy.com/blog/abc-analysis/

NetSuite. (2023). ABC analysis in inventory management: Benefits & best practices. NetSuite. https://www.netsuite.com/portal/resource/articles/inventory-management/abc-inventory-analysis.shtml

PMC. (2025). Implementing prescriber-pharmacist collaboration to improve evidence-based medication prescribing using asynchronous, non-interruptive electronic health record notifications. PubMed Central.

Rajalakshmi, M., Datchanamourtty, P., & Vasigar, P. (2024). Insights into medicine expiry awareness among the population of rural South India: A mixed-methods approach. Cureus, 16(9), Article e70314. https://doi.org/10.7759/cureus.70314

Remindax. (2026). Managing FDA pharmaceutical expiration dates: Compliance rules and modern tracking solutions. Remindax.

Shbaily, E. M., Dighriri, I. M., Alotaibi, N. S., Alqahtani, R. M., Mushawwal, A. M., Mohammed, A. G., Barwaished, G. S., Almalki, M. M., Alshammari, M., Alharbi, S. B., Almalki, S. M., Alatawi, H. A., Alsharif, S. A., & Almurayt, M. (2025). Effectiveness of pharmacy automation systems versus traditional systems in hospital settings: A systematic review. Cureus, 17(1), Article e77934. https://doi.org/10.7759/cureus.77934