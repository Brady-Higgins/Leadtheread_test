# OpenAI embedding
# Pinecone Vector DB

# database like Openlibrary for finding fiction books then match to an existing google library book
# match to wikipedia plot description
# segmentation
# add title to text pre embedding
# chatgpt generation of plots that don't exist

from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv
import os
import time



def embed(text, client):
    response = client.embeddings.create(
    input=text,
    model="text-embedding-ada-002"
    )
    return response.data[0].embedding

def init_pinecone():
    pinecone_key = os.getenv("PINECONE_KEY")
    pc = Pinecone(api_key=pinecone_key)
    index = pc.Index("leadtheread")
    time.sleep(1)
    return index 

def init_openai():
    openai_key = os.getenv("OPENAI_KEY")
    client = OpenAI(api_key=openai_key)
    return client

def upsert(index,embedding,title,ISBN,id):
    meta = {'title':title,'ISBN':ISBN}
    vector = [{
        'id':id,
        'values':embedding,
        'metadata': meta
    }]
    index.upsert(vectors=vector)

def query(index,embedding):
    resp = index.query(
        vector = embedding,
        top_k = 2,
        include_metadata=True
    )
    return resp


if __name__=="__main__":
    load_dotenv()
    openai_client = init_openai()
    index = init_pinecone()
    # text="""
    # While spending the summer with the Dursleys, the twelve-year-old Harry Potter is visited by Dobby, a house-elf. Dobby says Harry is in danger and must promise not to return to Hogwarts. When Harry refuses, Dobby uses magic to destroy a pudding made by Aunt Petunia. Believing that Harry created the mess, Uncle Vernon locks him in his room. The Ministry of Magic sends a notice accusing Harry of performing underage magic and threatening to expel him from Hogwarts. The Weasley brothers Ron, Fred, and George arrive in their father's flying car and take Harry to their home. When Harry and the Weasleys go to Diagon Alley for school supplies, they meet Gilderoy Lockhart, a celebrity author who is the new Defence Against the Dark Arts professor. At King's Cross station, Harry and Ron cannot enter Platform 9¾ to board the Hogwarts Express, so they fly to Hogwarts in the enchanted car. During the school year, Harry hears a strange voice emanating from the castle walls. Argus Filch's cat is found Petrified, along with a warning scrawled on the wall: "The Chamber of Secrets has been opened. Enemies of the heir, beware". Harry learns that the Chamber supposedly houses a monster that attacks Muggle-born students, and which only the Heir of Slytherin can control. During a Quidditch match, a rogue Bludger strikes Harry, breaking his arm. Professor Lockhart botches an attempt to mend it, which sends Harry to the hospital wing. Dobby visits Harry and reveals that he jinxed the Bludger and sealed the portal at King's Cross. He also tells Harry that house-elves are bound to serve a master, and cannot be freed unless their master gives them clothing. After another attack from the monster, students attend a defensive duelling class. During the class, Harry displays the rare ability to speak Parseltongue, the language of snakes. Moaning Myrtle, a ghost who haunts a bathroom, shows Harry and his friends a diary that was left in her stall. It belonged to Tom Riddle, a student who witnessed another student's death when the Chamber was last opened. During the next attack by the monster, Hermione Granger is Petrified. Harry and Ron discover that the monster is a Basilisk, a gigantic snake that can kill victims with a direct gaze and Petrify them with an indirect gaze. Harry realizes the Basilisk is producing the voice he hears in the walls. After Ron's sister Ginny is abducted and taken into the Chamber, Harry and Ron discover the Chamber entrance in Myrtle's bathroom. When they force Lockhart to enter with them, he confesses that the stories he told of his heroic adventures are fabrications. He attempts to erase the boys' memories, but his spell backfires and obliterates his own memory. Harry finds an unconscious Ginny in the Chamber. A manifestation of Tom Riddle appears and reveals that he is Lord Voldemort and the Heir of Slytherin. After explaining that he opened the Chamber, Riddle summons the Basilisk to kill Harry. Dumbledore's phoenix Fawkes arrives, bringing Harry the Sorting Hat. While Fawkes blinds the Basilisk, Harry pulls the Sword of Gryffindor from the Hat. He slays the serpent, then stabs the diary with a Basilisk fang, destroying it and the manifestation of Riddle. Later, Harry liberates Dobby by tricking his master into giving him clothing. At the end of the novel, the Petrified students are cured and Gryffindor wins the House Cup.
    # """
    # text1="""
    # Bert, an awkward and seemingly ordinary boy, has grown up in a world where magic is forbidden and considered a relic of the past. Raised in the strict confines of a boarding school, his life takes a sharp turn when a simple museum trip goes horribly wrong. An ancient artifact reacts to Bert in a way no one expects, and soon, he's thrown into a whirlwind adventure that reveals a startling truth: Bert isn't ordinary—he's deeply connected to the forgotten magic of the world. Rescued by Finch, a rogue adventurer with a flying ship, Bert finds himself pursued by the sinister Prince Voss. Voss is bent on controlling the remnants of magic to gain power, and he believes Bert holds the key to unlocking it. As Bert uncovers more about himself, he discovers his past is shrouded in mystery. He learns that he’s the last link to a magical lineage, and his abilities could bring magic back into the world—or destroy it entirely. With the help of Finch and his spirited crew, Bert embarks on a dangerous journey to uncover the truth about his heritage and the secret war between those who want to suppress magic and those who seek to reclaim it. Along the way, he faces treacherous skies, ancient conspiracies, and the realization that even his closest allies might have their own hidden agendas. In the climactic battle, Bert confronts Prince Voss, unlocking his full magical potential and proving that magic is not something to be feared but embraced. The story ends with the world poised on the brink of rediscovery, as Bert learns that his journey is only the beginning of a larger tale of magic’s return.
    # """
    # emb = embed(text=text1,client=openai_client)
    # print(emb)
    # upsert(index,emb,"The Boy Who Went Magic","9781338217148","2")
    query_embedding = embed("Magic boy goes on adventures at hogwarts.",openai_client)
    resp = query(index,query_embedding)
    print(resp)
    