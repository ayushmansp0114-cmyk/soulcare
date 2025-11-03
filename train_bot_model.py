import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
import os

# Training data - bot vs human patterns
data = {
    'username_pattern': [0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1],
    'email_suspicious': [0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1],
    'name_length': [10, 12, 3, 2, 11, 9, 4, 13, 8, 3, 10, 2, 11, 8, 3, 4, 12, 3, 9, 5],
    'age_suspicious': [0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1],
    'is_bot': [0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1]
}

df = pd.DataFrame(data)
X = df[['username_pattern', 'email_suspicious', 'name_length', 'age_suspicious']]
y = df['is_bot']

# Train RandomForest model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

# Create directory if not exists
os.makedirs('core', exist_ok=True)

# Save model
with open('core/bot_detection_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print('✅ ML Bot Detection Model Trained & Saved!')
print(f'Accuracy: {model.score(X, y) * 100:.2f}%')
