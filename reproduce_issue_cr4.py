from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans

def train_model():
    # Case 1: No params (Existing smell should catch this)
    clf1 = RandomForestClassifier()

    # Case 2: Some params, but maybe missing critical ones (New capability needed)
    # Let's say critical is 'n_estimators'
    clf2 = RandomForestClassifier(max_depth=5) 

    # Case 3: Critical param present
    clf3 = RandomForestClassifier(n_estimators=100)

    # Case 4: Another model
    # Let's say critical is 'n_clusters'
    km1 = KMeans()
    km2 = KMeans(random_state=42)
    km3 = KMeans(n_clusters=5)
