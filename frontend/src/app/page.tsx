export default function Home() {
  return (
    <main id="main-content" className="workspace" tabIndex={-1}>
      <section className="intro" aria-labelledby="page-title">
        <p className="eyebrow">Your next chapter</p>
        <h1 id="page-title">Define your ideal job.</h1>
        <p className="lead">
          Bring together the work you want to do and the life you want it to fit.
          Start with a rough idea and give it shape, one question at a time.
        </p>
        <p className="availability">The job-definition workspace is being prepared.</p>
      </section>
      <section className="workflow" aria-labelledby="workflow-title">
        <h2 id="workflow-title">A little clarity, step by step</h2>
        <ol className="steps">
          <li>
            <h3>Describe what matters</h3>
            <p>Consider responsibilities, compensation, location, and work–life balance. It is fine to have unanswered questions.</p>
          </li>
          <li>
            <h3>Add your background</h3>
            <p>A CV or profile can provide context. Your past experience and your future preferences each have their place.</p>
          </li>
          <li>
            <h3>Review and refine</h3>
            <p>Clarify your priorities and review your definition. Return to it as your goals develop.</p>
          </li>
        </ol>
      </section>
    </main>
  );
}
