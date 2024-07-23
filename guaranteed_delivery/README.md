# Guaranteed Delivery

Keeps your modmail bot from losing user messages during downtime. If any messages have been sent after since the last process message, the pugin will ensure they are all sent through modmail upon the bot coming online. 

## Installation
`{prefix}plugin add khakers/modmail-plugins/guaranteed_delivery`

The plugin will automatically begin

## Caveats
- Only the next 15 messages after the last processed message are retrieved, so its still possible some messages are missed if a large number have been sent
- Staff replies are not currently handled (anything in )
- Only existing threads are currently covered by guaranteed delivery. This means that any DMs to the bot from users that do not have an existing thread will not create one upon start.