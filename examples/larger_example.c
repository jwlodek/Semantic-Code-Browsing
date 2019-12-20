#include <stdio.h>
#include <ctype.h>
#include <stdlib.h>

//method that finds if there exists a student with a specific id
//@params: id -> id to check against
//@params: list -> doubly linked list  that stores all of the students
//@return: id_found -> -1 if id was not found, 0 if it was found.
int check_id_repeat(int id, struct student_list* list){
	struct student_records* current_link = list->head;
	//printf("the current head is id %d name %s %s\n",list->head->student->id, list->head->student->first_name,list->head->student->last_name);
	int id_found = -1;
	if(list->num_of_students>0){
		while(current_link != NULL){
			if(current_link->student->id==id){
				id_found = 0;
			}
			current_link = current_link->previous;
		}
	}
	//printf("checking id repeat and found %d\n",id_found);
	return id_found;
}

//method that finds a student with the same id
//@params: list -> a doubly linked list that holds all of the students
//@params: id -> the id to check against
//@return: *current_link -> the link in the list that holds the student
struct student_records* search_by_id(struct student_list* list, int id){
	struct student_records* current_link = list->head;
	if(list->num_of_students>0){
		while(current_link->previous!=NULL){
			if(current_link->student->id==id){
				return current_link;
			}
			current_link = current_link->previous;
		}
		if(current_link->student->id==id){
			return current_link;
		}
	}
	return NULL;
}

//method that searches for students with a specific last name
//@params: list -> doubly linked list of students
//@params: last_name -> char* to the name we are testing against
//@return: same_last_name -> an int pointer that points to the ids found students
int* search_by_name(struct student_list* list, char* last_name){
	int* same_last_name = calloc(list->num_of_students+1, sizeof(int));
	struct student_records* current_link = list->head;
	int counter = 0;
	if(list->num_of_students>0){
		while(current_link!=NULL){
			int temp = 0;
			int count = 0;
			do{
				if(*(current_link->student->last_name+count)!=*(last_name+count)){
					temp = -1;
				}
				count++;
			}while(*(last_name+count)!='\0');

			if(*(current_link->student->last_name+count)!='\0'){
				temp = -1;
			}

			if(temp==0){
				*(same_last_name+counter) = current_link->student->id;
				counter++;
			}
			current_link = current_link->previous;
		}
	}
	return same_last_name;
}

//function that searches for students by major
//@params: list -> doubly linked list of all students
//@params: major -> major that we are searching for
//@return: same_major -> int pointer that points to discovered ids
int* search_by_major(struct student_list* list, char* major){

	int* same_major = calloc(list->num_of_students+1 ,sizeof(int));
	struct student_records* current_link = list->head;
	int counter = 0;
	if(list->num_of_students>0){
		while(current_link!=NULL){
			int temp = 0;
			int i;
			for(i = 0; i< 3; i++){
				if(*(current_link->student->major+i)!=*(major+i)){
					temp = -1;
				}
			}
			if(temp==0){
				*(same_major+counter) = current_link->student->id;
				counter++;
			}
			current_link = current_link->previous;
		}
	}
	return same_major;
}

//function that changes the names into the proper form
void fix_names(char* name){
	int counter = 0;
	while(*(name+counter)!='\0'){
		if(counter==0){
			 if(*name>90){
				*name= *name-32;
			}
		}
		else{
			if(*(name+counter)<90){
				*(name+counter) = *(name+counter)+32;
			}
		}
		counter++;
	}
}

//function for making the major all caps
void fix_majors(char* major){
	int counter = 0;
	while(*(major+counter)!='\0'){
		if(*(major+counter)>90){
			*(major+counter) = *(major+counter)-32;
		}
		counter++;
	}
}

//method used for printing out information about a student
//@params: student -> pointer to student being printed
void print_student(struct student* student,FILE* file_point,int out_file){
	if(out_file==0){
		int id = student->id;
		char* first_name = student->first_name;
		char* last_name = student->last_name;
		float gpa = student->gpa;
		char* major = student->major;
		printf("%d %s %s %.2f %s\n", id, first_name,last_name, gpa, major);
	}
	else{
		int id = student->id;
		char* first_name = student->first_name;
		char* last_name = student->last_name;
		float gpa = student->gpa;
		char* major = student->major;
		fprintf(file_point, "%d %s %s %.2f %s\n", id, first_name,last_name, gpa, major);
	}

}

//function for printing out information about all of the students
//@params: list -> doubly linked list of all of the students
void print_all_students(struct student_list* list, FILE* file, int out_file){
	struct student_records* link = list->head;
	while(link!=NULL){
		print_student(link->student,file,out_file);
		link = link->previous;
	}
}


//function for freeing all allocated memory for the Linked list
//@params: list -> pointer to the doubly linked list
void free_list(struct student_list* list){
	struct student_records* link = list->head;
	while(link!=NULL){
		struct student_records* temp = link->previous;
		free(link->student->first_name);
		free(link->student->last_name);
		free(link->student->major);
		free(link->student);
		free(link);
		link = temp;
	}
	free(list);
}