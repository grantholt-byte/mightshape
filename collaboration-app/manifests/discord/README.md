# Discord package notes

`application-command.json` is the reviewable `/design-think` command contract. The registration script contains the same payload and the adapter tests fail if they drift.

`install.json` records the deliberately narrow Guild Install surface. MightShape uses signed HTTP interactions, buttons, and modals. It requests no Gateway intents and does not request Message Content.

The permission integer grants only View Channel, Send Messages, Attach Files, Create Public Threads, and Send Messages in Threads. Thread creation is opportunistic: unsupported channel types or a missing thread permission fall back to the initiating channel.
