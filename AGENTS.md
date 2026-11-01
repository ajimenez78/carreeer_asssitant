# Carreer assistant system

## General description
This is a carrerr assistan systemt that helps user to define his ideal job, select interesting offers, develop a plan for closing the gap to get one of those positins, prepare the user to pass the job interviews and once the job starts, helps to efficiently domain the daily work and develop a carreer continuous growth.

## Business requierements

### 1. Job definition
- The user can define its ideal job position
- If the initial description is vague, The system can make questions to the user to help him clarify
- Include not only job responsabilities. Also compensations like salary and life/work balance.
- An example of an initial, partially vague description is referenced in doc/ajimenez/MY_IDEAL_JOB.md
- In the job definition, the user can be able to provide it's background, uploading it's CV in PDF, doc or even markdonw format and additional documents like the LinkedIn profile.
- Also external links like Linkedin profile or personal websites are allowed
- Once the position is defined, it can be re-visited and refined latelly

### 2. Job finding
- The system provides an Agent that can actively  find for job positions across Internet. The defined job position is used as template for this search.
- In an initial phase, The main source for finding positions will be LinkedIn. If needed, the system will ask to connect to the user LinkedIn account for more accurate finding.
- An score of position vs ideal job descriptions will be provided
- The system will notify to the user with the most interesting offers
- The user can provide feedback to the system about the found offers. The system will learn of this feedback.

### 3. Closing the gap
- If there is a Gap between the User skills and the skills demanded for the job offers, the system could provide a skill development plan to the user
- The plan shouldn't be specific to a particular offer, but suitable for most of the offers that match more the ideal job definition.

### 4. Application tracking and interview preparation
- The system will provide a module for tracking the opened job application processes
- The system will provide an assistant for preparing the different job interviews in the process
- If a process ends without a real offer, the user could provide feedback to the system to enhance the career plan

### 5. Getting into the real job and further
- Once a job position is reached, the system will guide the user to be proficient in doing the real daily job
- The system will provide with a further develpment carrer plan for the user, in the current company or outside it, based on his goals, preferences and the market status

## Limitations
The business requiremens implementation will be incremental. We will start with a MVP that will only match with the first step, Job definition. But the initial design will take into account that the system will grouth with the rest of provided requirements

## Technical decisions
- It will be deployed to AWS cloud
- A NextJS frontend
- A Python backend
- You must decide if it is better to use AWS lambda and AWS services in general, or a Docker container instead. You can ask me any additional info you'll neeed.
- The solution should be tested locally, prior to the real Cloud deployment
- Use Amazon Bedrock as AI endpoint. The needed enpoints and credentials are provided in an .env file.
- Use a relational database for persistence

## Coding standards
1. For external libraries, use the most recent versions. Keep them updated.
2. Keep the code simple. Use good practices and proved design pattenrs, but do not overengineer. Simplfy and refactor when needed. No unnecessary defensive programming. No extra features. Follow SOLID principles and at the same time focus on simplicity.
3. Make and maintain useful unit and end-to-end tests. Try to ensure 80% of code coverage but do not force silly tests only to reach this goal. Keep them relevant and priorize useful test to coverage.
4. Keep README updated, simple and free of emojis.
5. When hitting issues, always identify root cause before trying a fix. Do not guess. Prove with evidence, then fix the root cause.

## Working documentation
All documents for planning and executing this project will be in the docs/ directory. Please review the docs/PLAN.md document before proceeding. the subfolder doc/ajimenez folder contains examples of an initial Job description, aCV and a LinkedIn profile