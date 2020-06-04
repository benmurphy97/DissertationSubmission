import numpy as np


# function to 
def get_popular_items(user_item_rating_matrix,item_cluster_memberships):

    popular_items = {}

    user_item_matrix = np.array(user_item_rating_matrix)
    user_item_matrix_T = user_item_matrix.T # transpose the matrix so it is rows of items, columns of users
    total_ratings = 0

    # for each cluster
    for key in item_cluster_memberships:

        # get the list of members of the cluster
        cluster_members = item_cluster_memberships[key] 

        # filtered_items is the user item matrix of items in a given cluster
        # each row is an item and each column is a users rating for the item
        filtered_items = user_item_matrix_T[cluster_members] 
        # print("\nfiltered_items",key,  filtered_items)



        # non_zeros is a list of the counts of non zero elements in each row
        # i.e. the the number of users who have rated the item in the past
        non_zeros = np.count_nonzero(filtered_items, axis=1) 
        # print("non_zeros", non_zeros)

        # average_number_of_ratings is the mean number of ratings for the items in the cluster
        average_number_of_ratings = non_zeros.mean() 
        # print("DEBUG", average_number_of_ratings)
        total_ratings+=average_number_of_ratings*len(cluster_members)

        # average_number_of_ratings = np.median(non_zeros) 

        # most_ratings is the item with the most number of ratings
        most_ratings = cluster_members[np.argmax(non_zeros)] # get id of item with most views

        # set the key with a tuple of: mean views in cluster, item id with most views
        popular_items[key] = (average_number_of_ratings, most_ratings)

    print("DEBUG", total_ratings)

    # returns dict of key:tuple
    return popular_items

# accepts a dict {'cluster key': ('mean cluster views','item id with most views in cluster')}
# returns item id with highest mean cluster views, and the dictionary back
def get_value_of_max_key_of_dict_of_tuple(a_dictionary):

    if len(a_dictionary) > 0:
        # # store keys and values
        v=list(a_dictionary.values())
        k=list(a_dictionary.keys())

        # get key of maximum cluster
        cluster_key_with_max = k[v.index(max(v))]

        # get the item id of maximum
        item_key_of_max = a_dictionary[cluster_key_with_max][1]
        del a_dictionary[cluster_key_with_max]

        # returns id and the dict
        return cluster_key_with_max, item_key_of_max, a_dictionary
    else:
        return None, None, a_dictionary

