

    # Utile quand on voudra afficher seulement une portion des personnages
    # On recup les X nodes de plus haut degre
    nodes = sorted(nodes, key=lambda t: t['size'], reverse=True)
    nodes_sliced = list(islice(nodes,150))
    nodes_sliced = sorted(nodes_sliced, key=lambda t: t['size'], reverse=False)
    nodes_sliced = list(islice(nodes_sliced,60))

    # On recupere juste les heros qui nous intéressent
    id_sliced_nodes = []
    for el in nodes_sliced : 
        id_sliced_nodes.append(el["id"])
    links_sliced = []
    for el in links : # el est un dictionnaire 
        if( (el["source"] in id_sliced_nodes) and (el["target"] in id_sliced_nodes) ):
            links_sliced.append(el)







##### Fonctions inutiles #####

def graph_sans_comics(graph):
    dico_nodes = {}
    plabel = graph.getStringProperty("viewLabel")
    # dictionnaire dans lequel la clé est une node 
    # et la valeur est la liste d'adjacence de distance 2 de cette node. 
    picon = graph.getStringProperty("viewIcon")
    # On ne s'intéresse qu'aux heros

    #for n in picon.getNodesEqualTo("md-human") :
    for n in graph.getNodes():
        dico_nodes[n] = []
        print(plabel[n])
        if(picon[n] == "md-human"):
            neigh = graph.getInOutNodes(n) 
            # On récupère tous les comics dans lequel le hero apparâit
            for v in neigh : 
                #on récupère tous les heros de ce comic, sauf n 
                #on les met dans la liste d'adj si ils n'y sont pas deja
                v_neigh = graph.getInOutNodes(v)
                for u in v_neigh : 
                    # Changer pour mettre un poids à la place
                    if( ( u not in dico_nodes[n] ) and (u != n) ):
                        dico_nodes[n].append(u)    
    return(dico_nodes)

def ini_nodes(g): #g est le graphe
    #compute node degree
    #metricprop = g.getDoubleProperty("viewMetric")
    #sizeprop = g["viewSize"]
    #g.applyDoubleAlgorithm("Degree", metricprop)
    #g.applySizeAlgorithm('Size Mapping')
    picon = g.getStringProperty("viewIcon")
    plabel = g.getStringProperty("viewLabel")
    
    # On cree le dictionnaire des nodes
    # Il faut faire un id pour ces nodes
    nodes_id = {} # dictionnaire, la node est la clé et la valeur est l'id de cette node
    nodes = [] # liste de dictionnaires. 
    # Il faut donner un id a toutes nos nodes avant de creer les liens
    id = 0
    for n in picon.getNodesEqualTo("md-human"):
        nodes_id[n] = id
        id = id + 1
        nodes.append( { "id" : nodes_id[n] , "name" : plabel[n], "size" : 5 }  )
        #nodes.append( { "id" : nodes_id[n] , "name" : plabel[n], "size" : round(sizeprop[n][0],2) }  )
        # sizeprop est un array avec 3 colonnes. Pour chaque n on a la taille en x, en y et en z
    
    ### Remarque ###
    #On peut juste mettre un int par exemple 1 pour la propriete size, vu qu on la change ensuite
    ### Remarque Fin ###
    return(nodes,nodes_id) 

def ini_links(neighbors,nodes_id,nodes):
    # On cree le dictionnaire des liens 
    # Attention, on doit prendre l'id des nodes et non la node 
    links = []
    for el in neighbors.keys() : #on fait un parcours sur les clés du dictionnaire
        id_source = nodes_id[el]
        for neigh in neighbors[el] :
            id_target = nodes_id[neigh]
            links.append( { "source" : id_source , "target" : id_target } )
        nodes[id_source]["size"] = len(neighbors[el])
    return(nodes,links)

def ini_links2(neighbors,nodes_id):
    # On cree le dictionnaire des liens 
    # Attention, on doit prendre l'id des nodes et non la node 
    links = []
    for el in neighbors.keys() : #on fait un parcours sur les clés du dictionnaire
        id_source = nodes_id[el]
        for neigh in neighbors[el] :
            id_target = nodes_id[neigh]
            links.append( { "source" : id_source , "target" : id_target } )
    return(links)


def nodes_sans_pers(g,nodes_id,node_personnage):
    picon = g.getStringProperty("viewIcon")
    plabel = g.getStringProperty("viewLabel")

    nodes = [] # liste de dictionnaires.
    nodes_sans_pers = []
    for n in picon.getNodesEqualTo("md-human"):
        nodes.append( { "id" : nodes_id[n] , "name" : plabel[n], "size" : 5 }  )
        if(n != node_personnage):
            nodes_sans_pers.append( { "id" : nodes_id[n] , "name" : plabel[n], "size" : 5 }  )
    return(nodes,nodes_sans_pers) 
    


def links_sans_pers(neighbors,nodes_id,nodes,node_personnage):
    links = []
    links_sans_pers = []
    for el in neighbors.keys() : #on fait un parcours sur les clés du dictionnaire
        id_source = nodes_id[el]
        for neigh in neighbors[el] :
            id_target = nodes_id[neigh]
            links.append( { "source" : id_source , "target" : id_target } )
            if( (el != node_personnage) and (neigh != node_personnage) ):
                links_sans_pers.append( { "source" : id_source , "target" : id_target } )        
        nodes[id_source]["size"] = len(neighbors[el])
    return(nodes,links,links_sans_pers)














