import csv
import sys

from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier

TEST_SIZE = 0.4


def main():

    # Check command-line arguments
    if len(sys.argv) != 2:
        sys.exit("Usage: python shopping.py data")

    # Load data from spreadsheet and split into train and test sets
    evidence, labels = load_data(sys.argv[1])
    X_train, X_test, y_train, y_test = train_test_split(
        evidence, labels, test_size=TEST_SIZE
    )

    # Train model and make predictions
    model = train_model(X_train, y_train)
    predictions = model.predict(X_test)
    sensitivity, specificity = evaluate(y_test, predictions)

    # Print results
    print(f"Correct: {(y_test == predictions).sum()}")
    print(f"Incorrect: {(y_test != predictions).sum()}")
    print(f"True Positive Rate: {100 * sensitivity:.2f}%")
    print(f"True Negative Rate: {100 * specificity:.2f}%")


def load_data(filename):
    """
    Load shopping data from a CSV file `filename` and convert into a list of
    evidence lists and a list of labels. Return a tuple (evidence, labels).

    evidence should be a list of lists, where each list contains the
    following values, in order:
        - Administrative, an integer
        - Administrative_Duration, a floating point number
        - Informational, an integer

        - Informational_Duration, a floating point number
        - ProductRelated, an integer
        - ProductRelated_Duration, a floating point number

        - BounceRates, a floating point number
        - ExitRates, a floating point number
        - PageValues, a floating point number

        - SpecialDay, a floating point number
        - Month, an index from 0 (January) to 11 (December)
        - OperatingSystems, an integer

        - Browser, an integer
        - Region, an integer
        - TrafficType, an integer

        - VisitorType, an integer 0 (not returning) or 1 (returning)
        - Weekend, an integer 0 (if false) or 1 (if true)

    labels should be the corresponding list of labels, where each label
    is 1 if Revenue is true, and 0 otherwise.
    """
    #USeful
    months = {"Jan": 0, "Feb": 1, "Mar": 2, "Apr": 3, "May": 4, "June": 5, "Jul": 6, "Aug": 7, "Sep": 8, "Oct": 9, "Nov": 10, "Dec": 11}
    boolvalues = {"TRUE": 1, "FALSE": 0}
    #Required lists
    Evidence = []
    Labels = []

    with open(filename, 'r') as file:

        reader = csv.DictReader(file)

        # Process each row into an evidence and label list
        for row in reader:
            row_evidence = []
            row_evidence.append(int(row["Administrative"]))
            row_evidence.append(float(row["Administrative_Duration"]))
            row_evidence.append(int(row["Informational"]))

            row_evidence.append(float(row["Informational_Duration"]))
            row_evidence.append(int(row["ProductRelated"]))
            row_evidence.append(float(row["ProductRelated_Duration"]))

            row_evidence.append(float(row["BounceRates"]))
            row_evidence.append(float(row["ExitRates"]))
            row_evidence.append(float(row["PageValues"]))

            row_evidence.append(float(row["SpecialDay"]))

            #Special Month value
            row_evidence.append(months[row["Month"]])
            row_evidence.append(int(row["OperatingSystems"]))

            row_evidence.append(int(row["Browser"]))
            row_evidence.append(int(row["Region"]))
            row_evidence.append(int(row["TrafficType"]))

            # Special visitortype value
            if row["VisitorType"] == "Returning_Visitor":
                row_evidence.append(1)
            else:
                row_evidence.append(0)

            # 1 if true, 0 otherwise
            row_evidence.append(boolvalues[row["Weekend"]])

            # Append the list into evidence
            Evidence.append(row_evidence)

            #Append this row's Label into label
            Labels.append(boolvalues[row["Revenue"]])

            # At evidence(17) the Labels length is 1
            if len(Evidence) == 16:
                x = 1

#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
    return (Evidence, Labels)

def train_model(evidence, labels):
    """
    Given a list of evidence lists and a list of labels, return a
    fitted k-nearest neighbor model (k=1) trained on the data.
    """

    model = KNeighborsClassifier(n_neighbors=1)
    model.fit(evidence, labels)
    return model



def evaluate(labels, predictions):
    """
    Given a list of actual labels and a list of predicted labels,
    return a tuple (sensitivity, specificity).

    Assume each label is either a 1 (positive) or 0 (negative).

    `sensitivity` should be a floating-point value from 0 to 1
    representing the "true positive rate": the proportion of
    actual positive labels that were accurately identified.

    `specificity` should be a floating-point value from 0 to 1
    representing the "true negative rate": the proportion of
    actual negative labels that were accurately identified.
    """

    # Total sample size
    t = len(labels)

    # Actual negatives
    negs = 0
    # Actual positives
    pos = 0
    for i in range(t):
        if labels[i] == 0:
            negs += 1
        else:
            pos += 1

    # Actual positives
    # True positives
    tp = 0
    # True negatives
    tn = 0
    for i in range(t):
        if (labels[i] == 1) and (predictions[i] == 1):
            tp += 1
        elif (labels[i] == 0) and (predictions[i] == 0):
            tn += 1

    # Calculate Sensitivity
    sensitivity  = float(tp/pos)
    # Calculate Specificity
    specificity = float(tn/negs)

    #Return
    return (sensitivity, specificity)


#--------------------------------------------------------------
#--------------------------------------------------------------


if __name__ == "__main__":
    main()
