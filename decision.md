kept tests in same dockerfile, can put in a seperate dockerfile, usually done in multistage builds to keep cleaner stages
kept everythign in main for server - file size if very small and managable, can be refractored later
not checking empty messages in internal api - usual case is internal api have correct payloads, maybe introduced if needed for rare/edgecases
