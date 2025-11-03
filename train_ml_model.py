import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Training data - legitimate vs bot registrations
data = {
    'username_pattern': [1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0],
    'email_suspicious': [0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1],
    'name_length': [8, 12, 3, 4, 10, 9, 2, 11, 8, 5, 9, 3, 10, 7, 4, 3, 11, 4, 9, 5],
    'age_suspicious': [0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1],
    'is_bot': [0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1]
}

df = pd.DataFrame(data)
X = df[['username_pattern', 'email_suspicious', 'name_length', 'age_suspicious']]
y = df['is_bot']

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

# Save model
with open('core/bot_detection_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print('✅ ML Model trained and saved!')
