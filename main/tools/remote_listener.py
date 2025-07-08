from firebase_admin import credentials, firestore
import firebase_admin
import os

class RemoteListener:
    def __init__(self, master):
        self.app = master
        self.listener_unsubscribe = None
        self.processed_docs = set()
        if not firebase_admin._apps:
            cred_path = os.path.join(self.app.data_folder, "firebase-service-account.json")
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        print("Connected to Firebase")
    
    def listen(self):
        if self.listener_unsubscribe is not None:
            return
            
        def on_new_command(col_snapshot, changes, read_time):
            for change in changes:
                if change.type.name == 'ADDED':
                    doc_id = change.document.id
                    doc_data = change.document.to_dict()
                    
                    if doc_id in self.processed_docs:
                        continue
                    
                    if not doc_data.get('processed', False):
                        if self.app.server.running:
                            self.processed_docs.add(doc_id)
                            self.app.remote_stop_requested.emit()
                            print(f"Remote stop command received (doc: {doc_id})")
                        
                        try:
                            change.document.reference.update({'processed': True})
                        except Exception as e:
                            print(f"Warning: Failed to update document {doc_id}: {e}")
                            self.processed_docs.discard(doc_id)
        
        self.listener_unsubscribe = self.db.collection('remote_commands').on_snapshot(on_new_command)
        print("Firebase listener started")
    
    def stop_listening(self):
        if self.listener_unsubscribe is not None:
            self.listener_unsubscribe.unsubscribe()
            self.listener_unsubscribe = None
            print("Firebase listener stopped")
        

if __name__ == "__main__":
    RemoteListener().listen()
