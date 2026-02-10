module.exports = {
  name: "exampleSkill",
  description: "A sample skill that echoes input.",
  // context: { message, emit, storage }
  run: async (context) => {
    const { message, emit, storage } = context;
    const reply = `Skill received: ${message}`;
    // Store a log entry
    await storage.appendLog(reply);
    // Emit back to UI if needed
    if (emit) emit('skill result', reply);
    return reply;
  }
};
