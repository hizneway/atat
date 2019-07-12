import { mount } from '@vue/test-utils'

import uploadinput from '../upload_input'

import { makeTestWrapper } from '../../test_utils/component_test_helpers'

const UploadWrapper = makeTestWrapper({
  components: { uploadinput },
  templatePath: 'upload_input_template.html',
})

const UploadErrorWrapper = makeTestWrapper({
  components: { uploadinput },
  templatePath: 'upload_input_error_template.html',
})

describe('UploadInput Test', () => {
  it('should show input and button when no attachment present', () => {
    const wrapper = mount(UploadWrapper, {
      propsData: {
        initialData: null,
      },
    })

    const fileInput = wrapper.find('input[type=file]').element
    expect(fileInput).not.toBe(undefined)
  })

  it('should show file name and hide input', () => {
    const wrapper = mount(UploadWrapper, {
      propsData: {
        initialData: 'somepdf.pdf',
      },
    })

    const fileInput = wrapper.find('input[type=file]').element
    const fileNameSpan = wrapper.find('.uploaded-file__name')

    expect(fileInput).toBe(undefined)
    expect(fileNameSpan.html()).toContain('somepdf.pdf')
  })

  it('should correctly display error treatment', () => {
    const wrapper = mount(UploadErrorWrapper)

    const messageArea = wrapper.find('.usa-input__message')
    expect(messageArea.html()).toContain('Test Error Message')
  })
})
