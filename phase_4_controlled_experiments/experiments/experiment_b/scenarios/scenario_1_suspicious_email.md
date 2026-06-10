# Suspicious Email

## Scenario Context

You, as a user, receive an email asking you to confirm your university password through a link.
Because the message looks suspicious, you contact the university support system and are connected with an IT security expert.

## Core Facts

- Do not click the link
- Do not enter credentials
- Forward email to IT security
- Delete the email
- Change password if link was clicked

## Matched Interaction

Each participant evaluates the matched condition corresponding to their selected communication persona.

### STJ User -> STJ Expert

> **User:**
> I received an email asking me to confirm my password. What should I do?

> **Expert:**
> Follow the official security procedure for suspicious emails.
>
> Step 1: Do not click the link in the message.
> Step 2: Do not enter your login credentials.
> Step 3: Forward the email to IT security for review.

> **User:**
> Should I delete the email after forwarding it?

> **Expert:**
> Step 4: After forwarding the email, delete it from your inbox to remove the risk of accidental interaction.

> **User:**
> What if I already clicked the link?

> **Expert:**
> Step 5: If the link was clicked at any point, change your password immediately.

> **User:**
> Is there anything else I should do?

> **Expert:**
> After completing these steps, the required security actions are finished and the incident is properly reported.

### NTP User -> NTP Expert

> **User:**
> I received an email asking me to confirm my password. What should I do?

> **Expert:**
> Emails that ask for password confirmation through links are commonly used in phishing attacks.
> The purpose of these messages is usually to capture login credentials.
> Because of that risk, you should not click the link or enter your credentials.
> The correct action is to forward the email to IT security so it can be analyzed.

> **User:**
> Should I delete the email after forwarding it?

> **Expert:**
> Yes. Deleting the email after forwarding it reduces the chance of accidental interaction and prevents repeated exposure to the suspicious message.

> **User:**
> What if I already clicked the link?

> **Expert:**
> If the link was already clicked, changing the password reduces the risk of unauthorized access to your account.

> **User:**
> Is there anything else I should do?

> **Expert:**
> After these steps are completed, the reported message can be investigated by IT security and the risk is minimized.

### NFJ User -> NFJ Expert

> **User:**
> I received an email asking me to confirm my password. What should I do?

> **Expert:**
> You did the right thing by asking first, because messages like this can sometimes be unsafe and it is important to stay cautious.
> The safest approach is not to click the link or enter your credentials, and to forward the email to IT security so they can review it.

> **User:**
> Should I delete the email after forwarding it?

> **Expert:**
> Yes, after forwarding it, deleting the email helps prevent accidental clicks and keeps your inbox safer.

> **User:**
> What if I already clicked the link?

> **Expert:**
> If you already clicked the link, changing your password is a good precaution and helps protect your account.

> **User:**
> Is there anything else I should do?

> **Expert:**
> After completing these steps, IT security will take care of the rest, so you have handled the situation properly.

### SFP User -> SFP Expert

> **User:**
> I received an email asking me to confirm my password. What should I do?

> **Expert:**
> Do not click the link.
> Do not enter your credentials.
> Forward the email to IT security.

> **User:**
> Should I delete the email after forwarding it?

> **Expert:**
> Delete the email after forwarding it.

> **User:**
> What if I already clicked the link?

> **Expert:**
> Change your password if you clicked the link.

> **User:**
> Is there anything else I should do?

> **Expert:**
> That completes the required actions.

## Mismatched Interaction

Each participant evaluates a deliberately non-matching expert communication style for comparison.

### STJ User -> NFJ Expert

> **User:**
> I received an email asking me to confirm my password. What should I do?

> **Expert:**
> You did the right thing by asking first, because messages like this can sometimes be unsafe and it is important to stay cautious.
> The safest approach is not to click the link or enter your credentials, and to send the email to IT security so they can check it.

> **User:**
> Should I delete the email after forwarding it?

> **Expert:**
> Yes, once you have forwarded the message, deleting it from your inbox helps prevent accidental clicks and keeps things safer.

> **User:**
> What if I already clicked the link?

> **Expert:**
> If you already clicked the link, changing your password is a good precaution and helps protect your account.

> **User:**
> Is there anything else I should do?

> **Expert:**
> After taking these steps, IT security will handle the rest, so you have done what is needed to keep your account secure.

### NTP User -> SFP Expert

> **User:**
> I received an email asking me to confirm my password. What should I do?

> **Expert:**
> Do not click the link.
> Do not enter your credentials.
> Forward the email to IT security.

> **User:**
> Should I delete the email after forwarding it?

> **Expert:**
> Delete the email after forwarding it.

> **User:**
> What if I already clicked the link?

> **Expert:**
> Change your password if you clicked the link.

> **User:**
> Is there anything else I should do?

> **Expert:**
> That completes the required actions.

### NFJ User -> SFP Expert

> **User:**
> I received an email asking me to confirm my password. What should I do?

> **Expert:**
> Do not click the link.
> Do not enter credentials.
> Forward the email to IT security.

> **User:**
> Should I delete the email after forwarding it?

> **Expert:**
> Delete the email after forwarding it.

> **User:**
> What if I already clicked the link?

> **Expert:**
> Change your password if you clicked the link.

> **User:**
> Is there anything else I should do?

> **Expert:**
> No further actions are required.

### SFP User -> NFJ Expert

> **User:**
> I received an email asking me to confirm my password. What should I do?

> **Expert:**
> You did the right thing by checking before taking action, because messages like this can sometimes be unsafe.
> To stay protected, avoid clicking the link or entering your login details, and send the email to IT security so they can examine it carefully.

> **User:**
> Should I delete the email after forwarding it?

> **Expert:**
> Yes, after forwarding the message, deleting it from your inbox helps reduce the chance of accidental clicks and keeps things more secure.

> **User:**
> What if I already clicked the link?

> **Expert:**
> If the link has already been clicked, changing your password is an important precaution and helps protect your account from possible misuse.

> **User:**
> Is there anything else I should do?

> **Expert:**
> After taking these steps, IT security will handle the rest, so you can feel confident that the situation has been addressed properly.
