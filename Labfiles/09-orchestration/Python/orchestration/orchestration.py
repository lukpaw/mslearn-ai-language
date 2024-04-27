from dotenv import load_dotenv
import os

from azure.ai.language.conversations import ConversationAnalysisClient
from azure.core.credentials import AzureKeyCredential


def main():
    try:
        # Get Configuration Settings
        load_dotenv()
        endpoint = os.getenv('CONVERSATION_ANALYSIS_ENDPOINT')
        credential = AzureKeyCredential(os.getenv("CONVERSATION_ANALYSIS_KEY"))
        project_name = os.getenv("CONVERSATION_ANALYSIS_PROJECT")
        deployment_name = os.getenv("CONVERSATION_ANALYSIS_DEPLOYMENT")

        client = ConversationAnalysisClient(endpoint, credential)

        while True:
            # User query input
            query = input("Input a query to your orchestration project (or 'quit' to exit): ")

            if query.lower() == "quit":
                break

            # Data preparation for analysis request
            data = {
                "analysisInput": {
                    "conversationItem": {
                        "text": query,
                        "id": "1",
                        "participantId": "1"
                    }
                },
                "parameters": {
                    "projectName": project_name,
                    "deploymentName": deployment_name,
                    "stringIndexType": "Utf16CodeUnit"
                },
                "kind": "Conversation"
            }

            # Send analysis request and get response
            response = client.analyze_conversation(data)

            if isinstance(response, dict):
                result = response
            else:
                raise Exception("Unexpected response format")

            # Extract top intent and orchestration prediction
            conversational_task_result = result["result"]
            orchestration_prediction = conversational_task_result["prediction"]
            top_intent = orchestration_prediction["topIntent"]

            print(f"The top intent was {top_intent}\n")
            print(f"The result from the connected project is as follows:\n")

            # Handle Conversation language understanding response
            if orchestration_prediction["intents"][top_intent]["targetProjectKind"] == "Conversation":
                conversation_prediction = orchestration_prediction["intents"][top_intent]["result"]["prediction"]

                print(f"\tTop Intent: {conversation_prediction['topIntent']}")
                print(f"\tIntents:")
                for intent in conversation_prediction["intents"]:
                    print(f"\t\tCategory: {intent['category']}")
                    print(f"\t\tConfidence: {intent['confidenceScore']}")
                    print()

                print(f"\tEntities:")
                for entity in conversation_prediction["entities"]:
                    print(f"\t\tCategory: {entity['category']}")
                    print(f"\t\tText: {entity['text']}")
                    print(f"\t\tOffset: {entity['offset']}")
                    print(f"\t\tLength: {entity['length']}")
                    print(f"\t\tConfidence: {entity['confidenceScore']}")
                    print()

                    if "resolutions" in entity:
                        for resolution in entity["resolutions"]:
                            if resolution["resolutionKind"] == "DateTimeResolution":
                                print(f"\t\t\tDatetime Sub Kind: {resolution['dateTimeSubKind']}")
                                print(f"\t\t\tTimex: {resolution['timex']}")
                                print(f"\t\t\tValue: {resolution['value']}")
                                print()

            # Handle Custom question answering response
            elif orchestration_prediction["intents"][top_intent]["targetProjectKind"] == "QuestionAnswering":
                question_answering_response = orchestration_prediction["intents"][top_intent]["result"]

                print("\tAnswers: \n")
                for answer in question_answering_response["answers"]:
                    print(f"\t\t{answer['answer']}")
                    print(f"\t\tConfidence: {answer['confidenceScore']}")
                    print(f"\t\tSource: {answer['source']}")
                    print()
            else:
                # Handle the case where intents or top_intent is invalid
                print(f"Warning: 'intents' or '{top_intent}' not found in orchestration_prediction")

    except Exception as ex:
        print(ex)
        raise ex


if __name__ == "__main__":
    main()
