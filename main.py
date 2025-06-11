import uuid
from agents.compiled_agents import ResearchAssistant
from agents.states import _initialize_state

Input = "what are the top 3 SOTA models in music generation, i want live information"


class RunResearchAssistant:

    def __init__(self, share=False):
        self.agent = ResearchAssistant()
        self.share = share
        self.threads = []
        self.thread_id = None
        self.config = {}

    def new_thread(self, Input: str):
        self.thread_id = str(uuid.uuid4())
        self.config = {"configurable": {"thread_id": self.thread_id}}
        state = _initialize_state(Input)
        return self.agent.main_agent.invoke(state, self.config)

    def existing_thread(self, Input: str):
        if not self.thread_id:
            raise ValueError("No existing thread_id to resume")
        snapshot = self.agent.main_agent.get_state(self.config)
        state = dict(snapshot.values)
        state["task"] = Input
        state["next_node"] = ""
        return self.agent.main_agent.invoke(state, config=self.config)

    def get_current_state(self, thread_id: str):
        config = {"configurable": {"thread_id": thread_id}}
        return self.agent.main_agent.get_state(config)


# for testing on new user.
if __name__ == "__main__":
    run_agent = RunResearchAssistant()

    response = run_agent.new_thread(Input)
    print("response:", response)
