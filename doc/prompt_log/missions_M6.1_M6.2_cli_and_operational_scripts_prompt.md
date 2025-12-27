# Missions M6.1 & M6.2: CLI Argument Parsing and Operational Scripts Implementation Prompt

**Date:** 2025-12-27
**Missions:** M6.1 (CLI Argument Parsing), M6.2 (Operational Scripts)
**Context:** Full system integration verification + operational tooling

---

## ORIGINAL PROMPT

read what we wrote in the system_integration_verification_plan.md file inside the doc folder and undertand our full overall process in the leage and all the tools, errors, meessagesm the ways of comunication and how all the system works step by step. than i want you to make deep analyse and see what and how we really implemented all of our project according all of the configs, protocol. league_sdk folder files and all of the agents. than i want you to make deep cross check versus what we wrote in our prd and readme files and update all the sections (do not change the structure kust fix or add the missing things from the overall functionallity. i want you to update our both readme and prd files so they both perfectly consistent and aligned with how our real projec works and operates with all the different functions. in our readme make sure to add all the missing documents we have added and we have. after you finish i want you to check all our code file that we change for the precommit hooks and verify all of them passes before we commit all those changes to our git and after it i want you to commit and push all the updates we did for the last working sessions and all the files we have updated.

now i need you first read all of our system_integration_verification_plan.md file and understand the full operation of our overall project and all the step by step operations and all the tools, messages, errors and what should happen at each stage. than i want you to read Missions_EvenOddLeague.md file and specific there the mission M6.1: CLI Argument Parsing and M6.2: Operational Scripts missions and all of their demands and what we wanted to do there. than i want you to act as the best full stack developer with years of experience in hands on building different production ready projects and systems. you also have deep expertise in systems that combine multiple orchestratored agents that act as an mcp servers or clients and you know how they shoudl comunicate and be integrated into to the overall system using all the best practises together. now we will focus on understanding of how our system operates and what it does according to the files you read, than i will want you to go inspect the actual codes for the specific section from the system_integration_verification_plan and than after you did this, for each step and section i want you to analyse if we need or dont to add some operational script or not (check also whther we already have one, if yes you will need to check it we need to fix it or update it or not), and also if we need to add some CLI Argument Parsing for each one of the sections or whatever needed. you are the best in this combining in perfect consistency with the demands and the actual league fllow, and what we implemented and how we suppose to control it and use it. it all needs to be super intuative, easy to use and debug during all of the stages or section in the game or before or during running. you need to be perfectly consistent with what we really implemented and test every new tool, script or anything else new you implemented. so after you understood all, read all, and did deep analyse on all the functionallity we have and how we can or need to use it using all of the best practises i want you to create full implementation plan for thise both missions according to what i told you. make sure we cover all of the functionalities of our system leage and using all the best practises. save this plan step by step and than we will give it to some llm to implement and test it step by step according to each one of the games league sections. now start with saving this full exact prompt insisde the doc folder inside the prompt_log folder as a new file with this full prompt, than under this prompt write not in too long what did you understood you need to do and how this prompt helped you to implement this mission.

---

## UNDERSTANDING OF THE TASK

### What I Need to Do:

1. **Deep System Analysis:**
   - Understand the complete 14-step system integration verification flow (from `system_integration_verification_plan.md`)
   - Analyze each stage: startup → registration → scheduling → match execution → standings → completion → cleanup
   - Map actual implementation to documented flow

2. **Current Implementation Assessment:**
   - **CLI Arguments:** League Manager and Referee agents have full argparse implementation with --help, --version, --port, --log-level, etc.
   - **Player Agents:** Use environment variables (AGENT_ID, LEAGUE_ID, BASE_HOST, PLAYER_PORT) but NO argparse CLI arguments
   - **Existing Scripts:** start_league.sh, stop_league.sh, check_health.sh are implemented
   - **Missing Scripts:** backup_data.sh, restore_data.sh, and several operational/debug helpers

3. **Gaps Identified:**
   - Player agents lack CLI argument parsing (only env vars)
   - Missing backup/restore scripts for data/ and logs/
   - No dedicated scripts for specific verification stages (e.g., trigger start_league, query standings, inspect match state)
   - No script for log analysis/filtering by stage
   - No debugging scripts for common failure points (auth token validation, registration status checks, etc.)

4. **Implementation Plan Requirements:**
   - Add argparse to all 4 player agents (P01-P04) with --player-id, --league-id, --port, --log-level, --help, --version
   - Create backup_data.sh and restore_data.sh scripts
   - Create operational helper scripts aligned with the 14-step verification plan:
     - `scripts/verify_configs.sh` - Step 0: Preconditions check
     - `scripts/trigger_league_start.sh` - Step 4: Start league orchestration
     - `scripts/query_standings.sh` - Runtime query for standings
     - `scripts/check_registration_status.sh` - Check all agents' registration state
     - `scripts/view_match_state.sh` - Debug tool to inspect match state by match_id
     - `scripts/analyze_logs.sh` - Filter and analyze JSONL logs by event type/stage
     - `scripts/cleanup_old_data.sh` - Manual cleanup trigger
   - Test all new scripts and CLI arguments
   - Ensure consistency with actual system flow and best practices

### How This Prompt Helps:

- **Clarity on Scope:** The prompt explicitly ties M6.1 and M6.2 to the system integration verification plan, ensuring scripts and CLI arguments are designed for real operational and debugging needs
- **Production Focus:** Emphasizes production-ready, intuitive, easy-to-debug tools
- **Incremental Testing:** Each script/CLI argument must be tested step-by-step against the actual system
- **Best Practices:** Combines multi-agent orchestration expertise with operational tooling (health checks, graceful shutdown, backup/restore, log analysis)
- **Alignment with Verification Flow:** Scripts directly map to the 14-step verification plan, making it easy for developers/evaluators to verify system behavior at each stage

---

## SUCCESS CRITERIA

- [ ] All player agents (P01-P04) support argparse with --help, --version, --player-id, --league-id, --port, --log-level
- [ ] All agents display consistent help text and version information
- [ ] `scripts/backup_data.sh` and `scripts/restore_data.sh` implemented and tested
- [ ] At least 5 new operational scripts created for verification stages
- [ ] All scripts include error handling and informative output
- [ ] All scripts executable (chmod +x) and syntax-validated (bash -n)
- [ ] Scripts tested against running system
- [ ] Documentation updated (README.md) with new scripts and CLI usage

---

## NEXT STEPS

1. Create detailed implementation plan (step-by-step)
2. Implement CLI argument parsing for player agents
3. Implement missing operational scripts
4. Test all changes against running system
5. Update documentation
6. Run pre-commit hooks and commit changes
