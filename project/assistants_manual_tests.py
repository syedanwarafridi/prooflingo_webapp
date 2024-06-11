from Assistants import text_tune_assistant, comparison_assistant, assistant, embed_tables_in_text, extract_text_with_table_tags



# embedded_source_text = embed_tables_in_text(source_text, source_tables)
# embedded_target_text = embed_tables_in_text(target_text, target_tables)



# for page_num, page_text in enumerate(embedded_source_text, start=1):
#     print(f"Source Page {page_num} Text:\n{page_text}\n")


# for page_num, page_text in enumerate(embedded_target_text, start=1):
#     print(f"Target Page {page_num} Text:\n{page_text}\n")


#now i have to pass the every source page and target page one by one
#and i will take response of model and append it to string everytime

# llm_response_history= ''
# for source_page, target_page in zip(embedded_source_text, embedded_target_text):
#     response = comparison_assistant(source_page, target_page, llm_response_history, 'nothing_context', 'spanish')
#     print('New Page response: ')
#     print(response)
#     llm_response_history += response + "\n"

# print('overall history')

# print(llm_response_history)



#--------------------------------text tunning assistant test-----------------------------------------------------------
# print(text_tune_assistant('justicia', 'Spanish'))



#-------------------------------AI assistant test---------------------------------------------------
# print(assistant('I am usman, I am very good boy.', 'underline name in the text and highligh any trade or characteristic'))