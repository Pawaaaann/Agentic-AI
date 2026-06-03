from google.ai.generativelanguage_v1beta3.services.model_service import ModelServiceClient

def main():
    client = ModelServiceClient()
    resp = client.list_models()
    print("Available models:")
    for m in resp:
        print(f"- name: {m.name}\n"
              f"  base_model_id: {m.base_model_id}\n"
              f"  version: {m.version}\n"
              f"  display_name: {m.display_name}\n"
              f"  supported_generation_methods: {m.supported_generation_methods}\n")

if __name__ == '__main__':
    main()
